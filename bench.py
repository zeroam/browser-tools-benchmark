#!/usr/bin/env python3
"""Q6 browser-tool benchmark harness.

Same model, same prompt, only the browser tool changes. See the Work Brief
"에이전트 브라우저 작업을 Playwright CLI로 옮기고 콘솔 로그인 상태를 유지한다" (Q6).

Subcommands:
  demo --parallel  run CLI v1 and v2 together, including servers and reports
  serve            start fixture + WebGames servers in the background
  versions         record tool/browser/model versions to results/versions.json
  schedule         write the fixed run schedule to results/schedule.json
  run [--only ID]  execute the schedule (skips finished runs, stops at the budget cap)
  one ID           execute a single scheduled run (pilot)
"""
import argparse
import fcntl
import hashlib
import json
import os
import random
import re
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "runs"
WORK = ROOT.parent / (ROOT.name + "-work")  # agent cwds live outside the harness tree (logs hold answers)
DOWNLOADS = WORK / "downloads"
WG_LOG = ROOT / "results/webgames.log"
RESULTS = ROOT / "results"
NODE_BIN = Path(shutil.which("node") or "/usr/bin/node").resolve().parent
GLOBAL_NM = Path(subprocess.check_output(["npm", "root", "-g"], text=True).strip())
LOCAL_BIN = Path.home() / ".local/bin"
PATH = os.environ.get("PATH", "")
MODEL = os.environ.get("BENCH_MODEL", "claude-sonnet-5-5")
BASE_TOOLS = "Bash,Read,Write,Edit,Glob,Grep"
FIX_PORT = 5320
WG_PORT = 5310
BUDGET_CAP = float(os.environ.get("BENCH_BUDGET_USD", "5"))
SEED = 20261016
EGO_BROWSER = Path(shutil.which("ego-browser") or str(LOCAL_BIN / "ego-browser"))
MCP_CLI = ROOT / "tools/node_modules/@playwright/mcp/cli.js"

ARMS = {
    "pwcli": {
        "label": "Playwright CLI",
        "skill": GLOBAL_NM / "@playwright/cli/node_modules/playwright-core/lib/tools/skills/playwright-cli",
        "tool": "the `playwright-cli` command (see the skill in your instructions)",
        "modes": {"headless": {}, "headed": {"PLAYWRIGHT_MCP_HEADLESS": "false"}},
    },
    "agentbrowser": {
        "label": "agent-browser",
        "skill": GLOBAL_NM / "agent-browser/skills/agent-browser",
        "tool": "the `agent-browser` command (see the skill in your instructions)",
        "modes": {"headless": {}, "headed": {"AGENT_BROWSER_HEADED": "1"}},
    },
    "ego": {
        "label": "ego lite",
        "skill": Path.home() / ".local/share/ego/ego-skills",
        "tool": "the `ego-browser` command (see the skill in your instructions)",
        "modes": {"headed": {}},  # no headless mode exposed; recorded as headed
    },
    "pwmcp": {
        "label": "Playwright MCP",
        "skill": None,
        "tool": "the Playwright MCP browser tools (mcp__playwright__*)",
        "modes": {"headless": ["--headless"], "headed": []},
    },
}
MAIN_MODE = {"pwcli": "headless", "agentbrowser": "headless", "ego": "headed", "pwmcp": "headless"}
HEADED_COMPARE_ARMS = ["pwcli", "agentbrowser"]  # ego has no headless mode, MCP is being removed
WEBGAMES_VARIANCE = ["buttons", "file-upload", "iframe-nest"]  # ids resolved from webgames-tasks.json

PREAMBLE = """You are completing a browser task on this Mac for an automated evaluation.
- Use {tool} for every browser interaction.
- Interact with pages the way a user would. Do not read page source code, JavaScript bundles, server code, or files outside the current directory to find answers. Do not use curl, wget, or scripts that download the site's files.
- Do not write your own browser automation with libraries such as Playwright, Puppeteer, or Selenium{f4_note}. Use only the browser tool named above.
- Keep any files you create inside the current directory.
- Finish your final message with one line in exactly this form: ANSWER: <value>
  If you could not complete the task, finish with: ANSWER: FAILED
"""


# ----------------------------------------------------------------------------- utils
def now():
    return time.time()


def admin_token():
    p = ROOT / ".admin-token"
    if not p.exists():
        p.write_text(secrets.token_hex(16))
        p.chmod(0o600)
    return p.read_text().strip()


def admin(method, path, body=None):
    req = urllib.request.Request(f"http://127.0.0.1:{FIX_PORT}/__admin/{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"X-Admin-Token": admin_token(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def run_env(extra=None):
    env = {k: v for k, v in os.environ.items()
           if not (k.startswith("ORCA_") or k.startswith("CLAUDE") or k.startswith("PLAYWRIGHT_")
                   or k.startswith("AGENT_BROWSER_") or k.startswith("FNM_MULTISHELL"))}
    env["PATH"] = PATH
    env["DISABLE_AUTOUPDATER"] = "1"
    env["TZ"] = "UTC"  # WebGames TodaysDate checks the UTC date
    env.update(extra or {})
    return env


def session_env(cwd):
    name = "bench-" + hashlib.sha256(str(Path(cwd).resolve()).encode()).hexdigest()[:12]
    return {"PLAYWRIGHT_CLI_SESSION": name, "AGENT_BROWSER_SESSION": name,
            "PLAYWRIGHT_MCP_OUTPUT_DIR": str(Path(cwd) / ".browser-output")}


def sh(cmd, cwd=None, env=None, timeout=60):
    if env is None:
        env = run_env(session_env(cwd) if cwd else None)
    try:
        r = subprocess.run(cmd, cwd=cwd, env=env or run_env(), capture_output=True, text=True, timeout=timeout,
                           shell=isinstance(cmd, str))
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return -1, "timeout"


def rand_code(prefix, n=6):
    return f"{prefix}-{secrets.token_hex(n // 2 + 1)[:n].upper()}"


# ----------------------------------------------------------------------------- processes
BROWSER_RE = re.compile(r"Google Chrome|Chromium|chrome-headless-shell|Chrome for Testing|ego Helper|ego lite\.app/Contents/MacOS/ego lite")
DAEMON_RE = re.compile(r"cliDaemon\.js|dashboardApp\.js|agent-browser|playwright-mcp|@playwright/mcp/cli\.js|ego lite\.app/Contents/MacOS/ego lite")
EGO_RE = re.compile(r"ego lite\.app/")


def ps():
    out = subprocess.run(["ps", "-axo", "pid=,ppid=,rss=,command="], capture_output=True, text=True).stdout
    procs = {}
    for line in out.splitlines():
        parts = line.strip().split(None, 3)
        if len(parts) == 4:
            procs[int(parts[0])] = (int(parts[1]), int(parts[2]), parts[3])
    return procs


def owned(procs, baseline, claude_pids, include_ego):
    """Processes that belong to this run: descendants of our claude processes, of tool daemons that
    appeared after the run started (they reparent to launchd), and (for the ego arm) the ego app."""
    roots = set(claude_pids)
    for pid, (ppid, _, cmd) in procs.items():
        if pid in baseline:
            continue
        if DAEMON_RE.search(cmd) and ppid == 1 and (str(WORK) in cmd or str(RUNS) in cmd):
            roots.add(pid)

    mine = set()
    for pid in procs:
        cur, seen = pid, 0
        while cur in procs and seen < 64:
            if cur in roots:
                mine.add(pid)
                break
            if cur in baseline and cur not in roots and not (include_ego and EGO_RE.search(procs[cur][2])):
                break
            cur = procs[cur][0]
            seen += 1
    return mine


class Sampler(threading.Thread):
    def __init__(self, baseline, include_ego, out_path):
        super().__init__(daemon=True)
        self.baseline, self.include_ego, self.out_path = baseline, include_ego, out_path
        self.claude_pids = set()
        self.stop_evt = threading.Event()
        self.max_browser_kb = 0
        self.max_tool_kb = 0
        self.max_browser_procs = 0

    def run(self):
        with open(self.out_path, "w") as f:
            while not self.stop_evt.is_set():
                procs = ps()
                mine = owned(procs, self.baseline, self.claude_pids, self.include_ego)
                b_kb = sum(procs[p][1] for p in mine if BROWSER_RE.search(procs[p][2]))
                t_kb = sum(procs[p][1] for p in mine if DAEMON_RE.search(procs[p][2]) and not BROWSER_RE.search(procs[p][2]))
                nb = sum(1 for p in mine if BROWSER_RE.search(procs[p][2]))
                self.max_browser_kb = max(self.max_browser_kb, b_kb)
                self.max_tool_kb = max(self.max_tool_kb, t_kb)
                self.max_browser_procs = max(self.max_browser_procs, nb)
                f.write(json.dumps({"t": round(now(), 1), "browser_kb": b_kb, "tool_kb": t_kb, "browser_procs": nb}) + "\n")
                f.flush()
                self.stop_evt.wait(1.0)


def main_browser_procs(procs, pids):
    """Top-level browser processes (not helpers/renderers)."""
    return [p for p in pids if BROWSER_RE.search(procs[p][2]) and "--type=" not in procs[p][2]]


# ----------------------------------------------------------------------------- arm plumbing
def arm_skill_file(arm):
    a = ARMS[arm]
    if not a["skill"]:
        return None
    out = RESULTS / "arms" / f"{arm}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    if not out.exists():
        body = (Path(a["skill"]) / "SKILL.md").read_text()
        out.write_text(f"# Browser tool for this session: {a['label']}\n\nThe official skill for this tool follows. "
                       f"Its skill directory (for relative references it mentions) is: {a['skill']}\n\n{body}")
    return out


def arm_mcp_file(arm, mode, run_dir, profile_dir, cwd):
    cfg = {"mcpServers": {}}
    if arm == "pwmcp":
        args = [str(MCP_CLI)] + ARMS[arm]["modes"][mode] + ["--user-data-dir", str(profile_dir),
                                                         "--output-dir", str(cwd / ".mcp-out")]
        cfg["mcpServers"]["playwright"] = {"command": str(NODE_BIN / "node"), "args": args}
    p = run_dir / "mcp.json"
    p.write_text(json.dumps(cfg))
    return p


def arm_env(arm, mode):
    m = ARMS[arm]["modes"][mode]
    return m if isinstance(m, dict) else {}


def tool_sessions(arm, cwd):
    """Browser sessions/spaces the tool still has open (tool-level leftover)."""
    if arm == "pwcli":
        _, out = sh(["playwright-cli", "list"], cwd=cwd)
        name = session_env(cwd)["PLAYWRIGHT_CLI_SESSION"]
        blocks = re.split(r"(?m)^- ", out)
        return sum(name in x and "status: open" in x for x in blocks), "scoped session: " + name
    if arm == "agentbrowser":
        _, out = sh(["agent-browser", "session", "list"], cwd=cwd)
        names = [l for l in out.splitlines() if l.startswith("  ") and l.strip()]
        return sum(session_env(cwd)["AGENT_BROWSER_SESSION"] in x for x in names), "scoped session"
    if arm == "ego":
        code, out = sh([str(EGO_BROWSER), "nodejs", "-e",
                        'const s=await listTaskSpaces();console.log(JSON.stringify(s.filter(x=>x.ownership!=="user").map(x=>({id:x.id,name:x.name,ownership:x.ownership,state:x.state}))))'],
                       cwd=cwd, timeout=60)
        try:
            spaces = json.loads(out.strip().splitlines()[-1])
            return len(spaces), out[-500:]
        except Exception:
            return -1, out[-500:]
    return 0, ""


def cleanup_tool(arm, cwd):
    if arm == "pwcli":
        sh(["playwright-cli", "close"], cwd=cwd, timeout=60)
    elif arm == "agentbrowser":
        sh(["agent-browser", "close"], cwd=cwd, timeout=60)
    elif arm == "ego":
        sh([str(EGO_BROWSER), "nodejs", "-e",
            'const s=await listTaskSpaces();for(const x of s){if(x.ownership==="user")continue;try{const t=await claimTaskSpace(x.id);await t.finish({keep:[]});}catch(e){console.log("ERR",x.id,String(e).slice(0,120))}}'],
           cwd=cwd, timeout=120)


def kill_owned(baseline, claude_pids, include_ego):
    procs = ps()
    mine = owned(procs, baseline, claude_pids, include_ego=False)  # never kill the ego app here
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in mine:
            if pid in baseline:
                continue
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass
        time.sleep(2)
        procs = ps()
        mine = {p for p in mine if p in procs}
        if not mine:
            break


def ego_restart():
    # The shared harness never quits a person's app or modifies global skills.
    pass


def ego_skill_guard():
    return False


# ----------------------------------------------------------------------------- stream parsing
SHORTCUT_RES = [
    (re.compile(r"\bcurl\b|\bwget\b|urllib|requests\.get|http\.client"), "http-client"),
    (re.compile(r"bench/browser-tools"), "harness-path"),
    (re.compile(r"view-source|document\.scripts|querySelectorAll\(\s*['\"]script|/assets/[^ ]*\.js|\.js['\"]?\s*\)\s*\.then"), "source-read"),
    (re.compile(r"fetch\(|XMLHttpRequest|/api/"), "api-fetch"),
    (re.compile(r"chromium\.launch|require\(['\"]playwright|from playwright|import playwright|puppeteer|selenium|webdriver"), "own-automation"),
]


TRAVERSAL_RE = re.compile(r"(^|[\s\"'=:(])\.\./|\bcd\s+\.\.(\s|$|/)|\bcd\s+~|~/bench|/Users/[^/]+/bench(?!/q6-work)")


def parse_stream(path, cwd, secret=None, allow_own_automation=False, leak_markers=()):
    msgs, order, tool_uses, results = {}, [], {}, []
    init = result = None
    first_secret_in_output = None
    secret_in_input_before_output = False
    seq = 0
    with open(path, errors="replace") as f:
        for line in f:
            try:
                ev = json.loads(line)
            except Exception:
                continue
            t = ev.get("type")
            if t == "system" and ev.get("subtype") == "init":
                init = ev
            elif t == "assistant":
                m = ev.get("message", {})
                mid = m.get("id")
                if mid not in msgs:
                    order.append(mid)
                if m.get("usage"):
                    msgs[mid] = m["usage"]
                for c in m.get("content", []) or []:
                    if c.get("type") == "tool_use" and c.get("id") not in tool_uses:
                        seq += 1
                        tool_uses[c["id"]] = {"seq": seq, "name": c.get("name"), "input": c.get("input")}
                        if secret and first_secret_in_output is None and secret in json.dumps(c.get("input")):
                            secret_in_input_before_output = True
            elif t == "user":
                content = ev.get("message", {}).get("content")
                if isinstance(content, list):
                    for c in content:
                        if c.get("type") != "tool_result":
                            continue
                        raw = c.get("content")
                        text, imgs = "", 0
                        if isinstance(raw, str):
                            text = raw
                        elif isinstance(raw, list):
                            for x in raw:
                                if x.get("type") == "text":
                                    text += x.get("text", "")
                                elif x.get("type") == "image":
                                    imgs += 1
                        if secret and first_secret_in_output is None and secret in text:
                            first_secret_in_output = seq
                        results.append({"is_error": bool(c.get("is_error")), "chars": len(text), "images": imgs,
                                        "head": text[:200], "tool_use_id": c.get("tool_use_id")})
            elif t == "result":
                result = ev

    def ctx(u):
        return (u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)) if u else 0

    per_msg = [ctx(msgs.get(m)) for m in order if msgs.get(m)]
    u = (result or {}).get("usage") or {}
    if not result:
        # Killed runs (timeout) never emit the final result event: fall back to the per-message usage.
        u = {k: sum((x or {}).get(k, 0) for x in msgs.values())
             for k in ("input_tokens", "output_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")}
    tokens = {
        "input": u.get("input_tokens", 0),
        "output": u.get("output_tokens", 0),
        "cache_creation": u.get("cache_creation_input_tokens", 0),
        "cache_read": u.get("cache_read_input_tokens", 0),
    }
    tokens["total"] = sum(tokens.values())
    tokens["fixed_overhead"] = per_msg[0] if per_msg else 0
    tokens["max_context"] = max(per_msg) if per_msg else 0
    tokens["tool_output_chars"] = sum(r["chars"] for r in results)
    tokens["tool_output_est_tokens"] = round(tokens["tool_output_chars"] / 3.5)
    tokens["tool_output_images"] = sum(r["images"] for r in results)

    calls = sorted(tool_uses.values(), key=lambda x: x["seq"])
    err_re = re.compile(r"^\s*(### Error|Error[: ]|error:|✗)", re.I)
    is_err = lambda r: r["is_error"] or bool(err_re.match(r["head"] or ""))
    tool_errors = sum(1 for r in results if is_err(r))
    errored = {r["tool_use_id"] for r in results if is_err(r)}
    id_by_seq = {v["seq"]: k for k, v in tool_uses.items()}
    # A retry is a call to the same tool right after that tool's previous call errored. Repeating an identical
    # call after success (e.g. a fresh snapshot) is normal work, not a retry.
    retries = sum(1 for prev, cur in zip(calls, calls[1:])
                  if prev["name"] == cur["name"] and id_by_seq[prev["seq"]] in errored)

    flags = []
    cwd_s = str(cwd)
    for c in calls:
        blob = json.dumps(c["input"])
        for rx, tag in SHORTCUT_RES:
            if tag == "own-automation" and allow_own_automation:
                continue
            if rx.search(blob.replace(cwd_s, "<cwd>")):
                flags.append({"tag": tag, "seq": c["seq"], "tool": c["name"], "input": blob[:300]})
        for mk in leak_markers:
            if mk in blob:
                flags.append({"tag": "leak-marker", "seq": c["seq"], "tool": c["name"], "input": f"{mk}: {blob[:250]}"})
        if c["name"] == "Bash" and TRAVERSAL_RE.search(str((c["input"] or {}).get("command", ""))):
            flags.append({"tag": "path-traversal", "seq": c["seq"], "tool": c["name"], "input": blob[:300]})
        if c["name"] in ("Read", "Grep", "Glob"):
            p = str((c["input"] or {}).get("file_path") or (c["input"] or {}).get("path") or "")
            if p.startswith("/") and not p.startswith(cwd_s):
                flags.append({"tag": "outside-cwd-file", "seq": c["seq"], "tool": c["name"], "input": blob[:300]})
    if secret_in_input_before_output:
        flags.append({"tag": "secret-before-seen", "seq": None, "tool": None, "input": ""})

    final = (result or {}).get("result") or ""
    m = re.findall(r"ANSWER:\s*(.+)", final)
    answer = m[-1].strip() if m else None
    answer_block = final[final.rfind("ANSWER:") + 7:].strip() if "ANSWER:" in final else None
    return {
        "init_model": (init or {}).get("model"),
        "init_tools": len((init or {}).get("tools", [])),
        "mcp_servers": (init or {}).get("mcp_servers"),
        "subtype": (result or {}).get("subtype"),
        "is_error": (result or {}).get("is_error"),
        "num_turns": (result or {}).get("num_turns"),
        "duration_ms": (result or {}).get("duration_ms"),
        "duration_api_ms": (result or {}).get("duration_api_ms"),
        "cost_usd": (result or {}).get("total_cost_usd") or 0.0,
        "tokens": tokens,
        "tool_calls": len(calls),
        "tool_errors": tool_errors,
        "retries": retries,
        "flags": flags,
        "final_text": final[-1500:],
        "answer": answer,
        "answer_block": answer_block,
        "secret_seen_in_output": first_secret_in_output is not None if secret else None,
    }


# ----------------------------------------------------------------------------- tasks
def load_webgames():
    return json.loads((ROOT / "webgames-tasks.json").read_text())


def wg_by_id(tid):
    for t in load_webgames():
        if t["id"] == tid:
            return t
    raise KeyError(tid)


def preamble(arm, f4=False):
    return PREAMBLE.format(tool=ARMS[arm]["tool"],
                           f4_note=" (except the Playwright Test file this task asks you to write)" if f4 else "")


def fmt_rows(rows):
    lines = ["| Symbol | Side | Qty | Avg price |", "|---|---|---|---|"]
    lines += [f"| {r['symbol']} | {r['side']} | {r['qty']} | {r['avg_price']} |" for r in rows]
    return "\n".join(lines)


def load_fixture_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("fx", ROOT / "fixtures/server.py")
    os.environ.setdefault("FIXTURE_ADMIN_TOKEN", admin_token())
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def mutate(field, value, rng):
    if field == "side":
        return "SHORT" if value == "LONG" else "LONG"
    digits = [i for i, ch in enumerate(value) if ch.isdigit()]
    i = digits[-1] if field == "avg_price" else digits[0]
    ch = str((int(value[i]) + rng.randint(1, 8)) % 10)
    if ch == value[i]:
        ch = str((int(ch) + 1) % 10)
    out = value[:i] + ch + value[i + 1:]
    return out


# ----------------------------------------------------------------------------- one run
RESULT_GRACE_S = 20  # past runs (209) never lingered more than 7.4 s after their result event


def stream_has_result(path):
    try:
        with open(path, "rb") as f:
            f.seek(max(0, path.stat().st_size - 65536))
            return b'"type":"result"' in f.read()
    except OSError:
        return False


def execute(agents, arm, mode, timeout, include_ego):
    """agents: list of (prompt, run_dir, cwd, budget, profile_dir, stream_name). Runs them concurrently."""
    baseline = set(ps().keys())
    first_dir = agents[0][1]
    sampler = Sampler(baseline, include_ego, first_dir / "mem.jsonl")
    procs = []
    t0 = now()
    for prompt, run_dir, cwd, budget, profile_dir, stream_name in agents:
        mcp = arm_mcp_file(arm, mode, run_dir, profile_dir, cwd)
        allowed = BASE_TOOLS + (",mcp__playwright" if arm == "pwmcp" else "")
        cmd = ["claude", "-p", prompt, "--model", MODEL, "--output-format", "stream-json", "--verbose",
               "--no-session-persistence", "--no-chrome", "--disable-slash-commands", "--setting-sources", "project",
               "--tools", BASE_TOOLS, "--allowedTools", allowed, "--strict-mcp-config", "--mcp-config", str(mcp),
               "--max-budget-usd", str(budget)]
        skill = arm_skill_file(arm)
        if skill:
            cmd += ["--append-system-prompt-file", str(skill)]
        (run_dir / f"{stream_name}.cmd.json").write_text(json.dumps(cmd[:2] + ["<prompt>"] + cmd[3:]))
        (run_dir / f"{stream_name}.prompt.txt").write_text(prompt)
        out = open(run_dir / f"{stream_name}.jsonl", "wb")
        err = open(run_dir / f"{stream_name}.stderr.txt", "wb")
        p = subprocess.Popen(cmd, cwd=cwd, env=run_env({**arm_env(arm, mode), **session_env(cwd)}), stdout=out, stderr=err,
                             start_new_session=True)
        procs.append((p, out, err))
        sampler.claude_pids.add(p.pid)
    sampler.start()
    timed_out, lingered = [], []
    for p, out, err in procs:
        # claude -p keeps running after its final result while a backgrounded Bash command is still alive
        # (seen with a hung ego-browser command). Once the result event is out, the agent is done: allow a
        # short grace, then end it the same way as a timeout and record it separately.
        result_at, ended = None, "exit"
        while p.poll() is None:
            if now() - t0 >= timeout:
                ended = "timeout"
                break
            if result_at is None and stream_has_result(Path(out.name)):
                result_at = now()
            if result_at is not None and now() - result_at > RESULT_GRACE_S:
                ended = "lingered"
                break
            time.sleep(1)
        timed_out.append(ended == "timeout")
        lingered.append(ended == "lingered")
        if ended != "exit":
            for sig in (signal.SIGTERM, signal.SIGKILL):
                try:
                    os.killpg(p.pid, sig)
                except (ProcessLookupError, PermissionError):
                    # macOS refuses killpg when a group member already exited oddly; signal the leader directly
                    try:
                        os.kill(p.pid, sig)
                    except ProcessLookupError:
                        pass
                time.sleep(3)
                if p.poll() is not None:
                    break
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                pass
        out.close()
        err.close()
    wall = now() - t0
    time.sleep(3)  # let tools settle before counting leftovers
    sampler.stop_evt.set()
    sampler.join(timeout=5)
    procs_now = ps()
    mine = owned(procs_now, baseline, sampler.claude_pids, include_ego=False)
    leftover_browsers = main_browser_procs(procs_now, mine)
    return {
        "baseline": baseline, "claude_pids": sampler.claude_pids, "timed_out": timed_out,
        "lingered_after_result": lingered, "wall_s": round(wall, 1),
        "max_browser_mb": round(sampler.max_browser_kb / 1024, 1), "max_tool_mb": round(sampler.max_tool_kb / 1024, 1),
        "max_browser_procs": sampler.max_browser_procs,
        "leftover_browser_procs": len(leftover_browsers),
    }


def finish_run(arm, cwd, ex):
    sessions, sess_out = tool_sessions(arm, cwd)
    cleanup_tool(arm, cwd)
    kill_owned(ex["baseline"], ex["claude_pids"], arm == "ego")
    guard = ego_skill_guard()
    return {"leftover_sessions": sessions, "leftover_sessions_raw": sess_out, "ego_skill_link_removed": guard}


def new_run_dir(rid):
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", rid):
        raise ValueError("Unsafe run ID")
    d = RUNS / rid
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    w = WORK / rid
    if w.exists():
        shutil.rmtree(w)
    w.mkdir(parents=True)
    return d


def work(rid, sub=None):
    w = WORK / rid / sub if sub else WORK / rid
    w.mkdir(parents=True, exist_ok=True)
    return w


def sweep_downloads(since, dest):
    """Move files the run dropped into ~/Downloads (e.g. FileCredentials in a real-profile browser)."""
    moved = []
    for f in DOWNLOADS.glob("credentials*"):
        try:
            if f.stat().st_mtime >= since:
                dest.mkdir(exist_ok=True)
                shutil.move(str(f), dest / f.name)
                moved.append(f.name)
        except FileNotFoundError:
            pass
    return moved


def wg_completions(offset, task_id):
    try:
        with open(WG_LOG, "rb") as f:
            f.seek(offset)
            lines = f.read().decode(errors="replace").splitlines()
    except FileNotFoundError:
        return False
    for line in lines:
        try:
            ev = json.loads(line)
        except Exception:
            continue
        if ev.get("event") == "completion" and ev.get("taskId") == task_id:
            return True
    return False


def run_webgames(item):
    arm, mode, tid = item["arm"], item["mode"], item["task"]
    t = wg_by_id(tid)
    d = new_run_dir(item["id"])
    cwd = work(d.name)
    for f in t.get("setup", []):
        shutil.copy(ROOT / f, cwd / Path(f).name)
    setup_note = ""
    if t.get("setup"):
        setup_note = "Files available in the current directory: " + ", ".join(f"./{Path(f).name}" for f in t["setup"]) + "\n"
    prompt = (preamble(arm) + f"\nTask: open {t['url']} and complete the challenge on that page. "
              f"The challenge: {t['description']}\nWhen you complete it, the page reveals a password. Report that password.\n"
              + setup_note)
    wg_off = WG_LOG.stat().st_size if WG_LOG.exists() else 0
    t_start = now()
    ex = execute([(prompt, d, cwd, 1.0, d / "profile", "stream")], arm, mode, 300, arm == "ego")
    fin = finish_run(arm, cwd, ex)
    fin["downloads_swept"] = sweep_downloads(t_start, d / "swept-downloads")
    markers = [x for x in t.get("leak_markers", []) if x != t["password"]]
    m = parse_stream(d / "stream.jsonl", cwd, secret=t["password"], leak_markers=markers)
    ans = m["answer"]
    completed = wg_completions(wg_off, t["id"])
    success = bool(ans) and t["password"] in ans
    claimed = bool(ans) and ans.upper() != "FAILED"
    if success and not completed:
        m["flags"].append({"tag": "no-completion-event", "seq": None, "tool": None, "input": ""})
    judge = {"success": success, "claimed": claimed, "false_success": claimed and not success,
             "expected": t["password"], "got": ans, "completion_logged": completed}
    return d, ex, fin, [m], judge


def fail_type(m, ex, judge):
    if judge["success"]:
        return None
    if any(ex["timed_out"]):
        return "timeout"
    if m and m.get("subtype") and m["subtype"] != "success":
        return m["subtype"]
    if judge.get("claimed"):
        return "wrong-answer"
    return "gave-up"


def run_f1(item):
    arm, mode = item["arm"], item["mode"]
    d = new_run_dir(item["id"])
    cwd = work(d.name)
    (cwd / "state").mkdir()
    ns = f"f1-{arm}-{item['rep']}-{secrets.token_hex(3)}".lower()
    user = f"operator-{secrets.token_hex(2)}"
    pw = secrets.token_urlsafe(9)
    code = rand_code("ST")
    admin("POST", "ns", {"ns": ns, "kind": "f1", "config": {"user": user, "password": pw, "code": code}})
    url = f"http://{ns}.localhost:{FIX_PORT}"
    p1 = (preamble(arm) + f"\nTask: open {url}/ and register the bot connection using ID `{user}` and password `{pw}` "
          f"(keep the Server URL field as it is). Confirm that {url}/status shows a status code.\n"
          "Then save this browser's login state (cookies and site storage) under ./state/ in the current directory, "
          "using your browser tool's own way of saving state, so that a later, separate session can reuse the login "
          "without the password.\nReport the status code you saw.\n")
    (d / "r1").mkdir()
    (d / "r2").mkdir()
    ex1 = execute([(p1, d / "r1", cwd, 1.0, d / "profile", "stream")], arm, mode, 300, arm == "ego")
    fin1 = finish_run(arm, cwd, ex1)
    m1 = parse_stream(d / "r1/stream.jsonl", cwd)
    # Browser restart between sessions.
    if arm == "ego":
        ego_restart()
    t_mark = now()
    p2 = (preamble(arm) + f"\nTask: a previous session registered a bot connection at {url}/ and saved the browser "
          "login state under ./state/ in the current directory. You do not have the password and must not ask for it. "
          f"Restore the saved login state with your browser tool, open {url}/status, and report the status code shown.\n")
    ex2 = execute([(p2, d / "r2", cwd, 1.0, d / "profile", "stream")], arm, mode, 300, arm == "ego")
    fin2 = finish_run(arm, cwd, ex2)
    m2 = parse_stream(d / "r2/stream.jsonl", cwd)
    log = admin("GET", f"ns/{ns}")["log"]
    relogin = any(e["event"] == "login_ok" and e["t"] >= t_mark for e in log)
    first_login = any(e["event"] == "login_ok" and e["t"] < t_mark for e in log)
    ans = m2["answer"]
    success = bool(ans) and code in ans and not relogin
    claimed = bool(ans) and ans.upper() != "FAILED"
    # State file security: where did the login state land, permissions, plaintext password?
    sec = []
    for f in sorted(cwd.rglob("*")):
        if f.is_file() and not f.is_symlink():
            try:
                data = f.read_bytes()
            except Exception:
                continue
            if pw.encode() in data or "sid" in data.decode(errors="ignore")[:200000]:
                sec.append({"path": str(f.relative_to(cwd)), "mode": oct(f.stat().st_mode & 0o777), "bytes": len(data),
                            "plaintext_password": pw.encode() in data})
    judge = {"success": success, "claimed": claimed, "false_success": claimed and not success,
             "expected": code, "got": ans, "relogin_in_run2": relogin, "run1_logged_in": first_login,
             "run1_answer": m1["answer"], "state_files": sec}
    return d, [ex1, ex2], [fin1, fin2], [m1, m2], judge


def run_f2(item):
    arm, mode = item["arm"], item["mode"]
    d = new_run_dir(item["id"])
    ns = f"f2-{arm}-{item['rep']}-{secrets.token_hex(3)}".lower()
    users = {f"user-{x}": {"password": secrets.token_urlsafe(9), "code": rand_code("ME")} for x in "abc"}
    admin("POST", "ns", {"ns": ns, "kind": "f2", "config": {"users": users}})
    url = f"http://{ns}.localhost:{FIX_PORT}"
    agents = []
    for u, v in users.items():
        sub = d / u
        sub.mkdir(parents=True)
        prompt = (preamble(arm) + "\nContext: two other agents are running on this Mac at the same time, each using the "
                  "same browser tool, each signed in to the same site as a different user. Do not interfere with them, "
                  "and make sure they cannot interfere with you.\n"
                  f"Task: sign in at {url}/ with ID `{u}` and password `{v['password']}`, then open {url}/me and read the "
                  f"code shown for {u}. Before answering, reload {url}/me once more and confirm it still shows {u}. "
                  "Report the code.\n")
        agents.append((prompt, sub, work(d.name, u), 1.0, sub / "profile", "stream"))
    ex = execute(agents, arm, mode, 300, arm == "ego")
    fins = [finish_run(arm, a[2], ex) for a in agents[:1]]
    for a in agents[1:]:
        cleanup_tool(arm, a[2])
    ms, per = [], []
    for (u, v), a in zip(users.items(), agents):
        m = parse_stream(a[1] / "stream.jsonl", a[2])
        ms.append(m)
        ok = bool(m["answer"]) and v["code"] in m["answer"]
        per.append({"user": u, "ok": ok, "got": m["answer"], "expected": v["code"]})
    success = all(p["ok"] for p in per)
    claimed = all(bool(m["answer"]) and m["answer"].upper() != "FAILED" for m in ms)
    judge = {"success": success, "claimed": claimed, "false_success": any(
        (bool(m["answer"]) and m["answer"].upper() != "FAILED" and not p["ok"]) for m, p in zip(ms, per)),
             "per_agent": per}
    return d, [ex], fins, ms, judge


FIELD_ALIASES = {"qty": "qty", "quantity": "qty", "size": "qty", "avg_price": "avg_price", "avg price": "avg_price",
                 "average price": "avg_price", "avgprice": "avg_price", "price": "avg_price", "avg": "avg_price",
                 "side": "side", "direction": "side"}


def norm_field(f):
    key = str(f).strip().lower().replace("-", " ").replace("_", " ")
    return FIELD_ALIASES.get(key, FIELD_ALIASES.get(key.replace(" ", "_"), key))


def judge_f3(ans, plant, shot_ok):
    items = None
    if ans and ans.upper() != "FAILED":
        try:
            parsed = json.loads(ans[ans.index("["): ans.rindex("]") + 1])
            items = parsed if isinstance(parsed, list) else None
        except Exception:
            items = None
    hit = extra = 0
    for it in items or []:
        if (isinstance(it, dict) and str(it.get("symbol", "")).upper() == plant["symbol"]
                and norm_field(it.get("field")) == plant["field"]
                and str(it.get("actual", "")).strip().upper() == plant["actual"].upper()):
            hit += 1
        else:
            extra += 1
    success = hit == 1 and extra == 0 and shot_ok
    claimed = bool(ans) and ans.upper() != "FAILED"
    return {"success": success, "claimed": claimed, "false_success": claimed and not success, "plant": plant,
            "got": ans, "parsed": items is not None, "hit": hit, "fabricated_or_wrong": extra, "screenshot_ok": shot_ok}


def run_f3(item, fx):
    arm, mode = item["arm"], item["mode"]
    rng = random.Random(f"{SEED}-{item['id']}")
    d = new_run_dir(item["id"])
    cwd = work(d.name)
    (cwd / "out").mkdir()
    bot = rng.choice(["b1", "b2"])
    rows = fx.BASE_POSITIONS[bot]
    row = rng.choice(rows)
    field = rng.choice(["qty", "avg_price", "side"])
    plant = {"bot": bot, "symbol": row["symbol"], "field": field, "expected": row[field],
             "actual": mutate(field, row[field], rng)}
    ns = f"f3-{arm}-{item['rep']}-{secrets.token_hex(3)}".lower()
    admin("POST", "ns", {"ns": ns, "kind": "f3", "config": {"plant": plant}})
    name = next(b["name"] for b in fx.BOTS if b["id"] == bot)
    url = f"http://{ns}.localhost:{FIX_PORT}"
    prompt = (preamble(arm) + f"\nTask: open the trading bot dashboard at {url}/. Open the detail page of the bot "
              f"`{name}` and read its positions table. Compare it with the expected positions below and report every "
              "difference. Also save a screenshot of that detail page to ./out/detail.png.\n\n"
              f"Expected positions for {name}:\n{fmt_rows(rows)}\n\n"
              "Report the differences as a JSON list on the ANSWER line, each item "
              '{"symbol": ..., "field": "side"|"qty"|"avg_price", "expected": ..., "actual": ...}. '
              "If there are no differences, use ANSWER: []\n")
    ex = execute([(prompt, d, cwd, 1.0, d / "profile", "stream")], arm, mode, 300, arm == "ego")
    fin = finish_run(arm, cwd, ex)
    m = parse_stream(d / "stream.jsonl", cwd)
    png = cwd / "out/detail.png"
    shot_ok = png.exists() and png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n" and png.stat().st_size > 2000
    judge = judge_f3(m["answer"], plant, shot_ok)
    return d, ex, fin, [m], judge


PW_CONFIG = """import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  retries: 0,
  reporter: 'line',
  use: { channel: 'chrome', headless: true },
});
"""


def run_f4(item, fx):
    arm, mode = item["arm"], item["mode"]
    rng = random.Random(f"{SEED}-{item['id']}")
    d = new_run_dir(item["id"])
    cwd = work(d.name)
    (cwd / "e2e").mkdir()
    (cwd / "playwright.config.ts").write_text(PW_CONFIG)
    (cwd / "package.json").write_text(json.dumps({"name": "e2e-task", "private": True}))
    (cwd / "node_modules").symlink_to(ROOT / "tools/node_modules")
    bot = rng.choice(["b1", "b2"])
    rows = fx.BASE_POSITIONS[bot]
    name = next(b["name"] for b in fx.BOTS if b["id"] == bot)
    ns = f"f4-{arm}-{item['rep']}-{secrets.token_hex(3)}".lower()
    admin("POST", "ns", {"ns": ns, "kind": "f4", "config": {"mode": "normal", "target": bot}})
    url = f"http://{ns}.localhost:{FIX_PORT}"
    prompt = (preamble(arm, f4=True) + f"\nTask: write a Playwright Test spec at ./e2e/positions.spec.ts for the trading "
              f"bot dashboard at {url}/. The test must: open the bot list at {url}/, click the bot `{name}` to open its "
              "detail page, and verify that the positions table shows exactly these rows:\n\n"
              f"{fmt_rows(rows)}\n\n"
              "The test must fail if any value in the table differs, or if clicking the bot does not open that bot's "
              "detail page. Explore the app with your browser tool first. @playwright/test is already installed here and "
              "./playwright.config.ts is set up; you may run `npx playwright test` to check the spec passes.\n"
              "Finish with ANSWER: DONE when the spec is written.\n")
    ex = execute([(prompt, d, cwd, 2.0, d / "profile", "stream")], arm, mode, 600, arm == "ego")
    fin = finish_run(arm, cwd, ex)
    m = parse_stream(d / "stream.jsonl", cwd, allow_own_automation=True)
    spec = cwd / "e2e/positions.spec.ts"
    outcomes = {}
    if spec.exists():
        for mode_name in ("normal", "bug-value", "bug-nav"):
            admin("POST", f"ns/{ns}/mode", {"mode": mode_name})
            code, out = sh(["npx", "playwright", "test", "e2e/positions.spec.ts"], cwd=cwd, timeout=180)
            outcomes[mode_name] = {"exit": code, "tail": out[-800:]}
        admin("POST", f"ns/{ns}/mode", {"mode": "normal"})
    success = (spec.exists() and outcomes.get("normal", {}).get("exit") == 0
               and outcomes.get("bug-value", {}).get("exit") not in (0, None)
               and outcomes.get("bug-nav", {}).get("exit") not in (0, None))
    claimed = bool(m["answer"]) and m["answer"].upper() != "FAILED"
    judge = {"success": success, "claimed": claimed, "false_success": claimed and not success,
             "spec_exists": spec.exists(), "outcomes": outcomes}
    return d, ex, fin, [m], judge


# ----------------------------------------------------------------------------- v2 tasks (harder, fixed 2026-10-16)
PREAMBLE_V2_EXTRA = "- When you are done, close any browser, session, or task space you opened.\n"
H1_K_SEQ = [2, 0, 3]  # planted mismatches per rep (rep 0, 1, 2); includes a no-mismatch run
LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def preamble_v2(arm, f4=False):
    return preamble(arm, f4) + PREAMBLE_V2_EXTRA


def extract_json(block):
    """First JSON value in the ANSWER block (allows code fences and multi-line JSON)."""
    if not block:
        return None
    b = re.sub(r"```(?:json)?", "", block).strip()
    for opener, closer in (("[", "]"), ("{", "}")):
        i = b.find(opener)
        if i < 0:
            continue
        depth = 0
        for j in range(i, len(b)):
            if b[j] == opener:
                depth += 1
            elif b[j] == closer:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(b[i:j + 1])
                    except Exception:
                        break
    return None


def tickers(rng, n):
    out = set()
    while len(out) < n:
        out.add("".join(rng.choice(LETTERS) for _ in range(rng.choice([3, 4]))) + "USDT")
    return sorted(out)


def same_value(a, b):
    a, b = str(a).strip().upper(), str(b).strip().upper()
    if a == b:
        return True
    try:
        return float(a.replace(",", "")) == float(b.replace(",", ""))
    except ValueError:
        return False


def h1_data(rng):
    names = ["alpha-trend", "beta-revert", "gamma-carry", "delta-breakout", "epsilon-grid", "zeta-basis"]
    bots = [{"id": f"b{i+1}", "name": n, "status": rng.choice(["Running", "Running", "Stopped"])} for i, n in enumerate(names)]
    target = rng.choice(bots)
    rows = {}
    for b in bots:
        n = 400 if b is target else rng.randint(25, 60)
        rs = []
        for sym in tickers(rng, n):
            qty = f"{rng.uniform(0.01, 5000):.{rng.choice([0, 2, 3])}f}"
            avg = f"{rng.uniform(0.01, 70000):.{rng.choice([2, 3, 4])}f}"
            mark = f"{float(avg) * rng.uniform(0.95, 1.05):.4f}"
            rs.append({"symbol": sym, "side": rng.choice(["LONG", "SHORT"]), "qty": qty, "avg_price": avg,
                       "mark": mark, "upnl": f"{rng.uniform(-900, 900):.2f}",
                       "opened": f"2026-10-{rng.randint(1, 15):02d} {rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}"})
        rows[b["id"]] = rs
    return bots, target, rows


def run_h1(item):
    arm, mode = item["arm"], item["mode"]
    rng = random.Random(f"{SEED}-v2-{item['id']}")
    d = new_run_dir(item["id"])
    cwd = work(d.name)
    bots, target, rows = h1_data(rng)
    expected_rows = [dict(r) for r in rows[target["id"]]]
    k = H1_K_SEQ[item["rep"] % len(H1_K_SEQ)]
    plants = []
    for r in rng.sample(rows[target["id"]], k):
        field = rng.choice(["side", "qty", "avg_price"])
        new = mutate(field, r[field], rng)
        plants.append({"symbol": r["symbol"], "field": field, "expected": r[field], "actual": new})
        r[field] = new  # the page shows the mutated value; the file keeps the original
    page_rows = {bid: sorted(rs, key=lambda r: -float(r["qty"])) for bid, rs in rows.items()}
    with open(cwd / "expected_positions.csv", "w") as f:
        f.write("symbol,side,qty,avg_price\n")
        for r in sorted(expected_rows, key=lambda r: r["symbol"]):
            f.write(f"{r['symbol']},{r['side']},{r['qty']},{r['avg_price']}\n")
    ns = f"h1-{arm}-{item['rep']}-{secrets.token_hex(3)}".lower()
    admin("POST", "ns", {"ns": ns, "kind": "h1", "config": {"bots": bots, "target": target["id"], "rows": page_rows}})
    url = f"http://{ns}.localhost:{FIX_PORT}"
    prompt = (preamble_v2(arm) + f"\nTask: open the trading bot dashboard at {url}/ and open the detail page of the bot "
              f"`{target['name']}`. Compare its positions table with ./expected_positions.csv (columns: symbol, side, "
              "qty, avg_price). The page lists positions in a different order and shows extra columns you should ignore.\n"
              "Report every position field that differs, as a JSON list on the ANSWER line, each item "
              '{"symbol": ..., "field": "side"|"qty"|"avg_price", "expected": <value in the file>, "actual": <value on the page>}. '
              "If nothing differs, use ANSWER: []\n")
    ex = execute([(prompt, d, cwd, 2.0, d / "profile", "stream")], arm, mode, 600, arm == "ego")
    fin = finish_run(arm, cwd, ex)
    m = parse_stream(d / "stream.jsonl", cwd)
    got = extract_json(m["answer_block"])
    want = {(p["symbol"], p["field"], p["actual"]) for p in plants}
    found, extra = set(), 0
    if isinstance(got, list):
        for it in got:
            if not isinstance(it, dict):
                extra += 1
                continue
            key = next((w for w in want if w[0] == str(it.get("symbol", "")).upper() and w[1] == norm_field(it.get("field"))
                        and same_value(w[2], it.get("actual", ""))), None)
            if key and key not in found:
                found.add(key)
            else:
                extra += 1
    success = isinstance(got, list) and found == want and extra == 0
    claimed = bool(m["answer"]) and m["answer"].upper() != "FAILED"
    judge = {"success": success, "claimed": claimed, "false_success": claimed and not success, "planted": plants,
             "parsed": got is not None, "hits": len(found), "missed": len(want) - len(found), "fabricated_or_wrong": extra}
    return d, ex, fin, [m], judge


def h2_data(rng):
    names = ["alpha-trend", "beta-revert", "gamma-carry", "delta-breakout", "epsilon-grid"]
    zero = rng.randrange(len(names))
    bots = []
    for i, n in enumerate(names):
        orders = []
        for _ in range(0 if i == zero else rng.randint(2, 7)):
            orders.append({"id": f"ORD-{rng.randint(10000, 99999)}", "symbol": rng.choice(["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]),
                           "side": rng.choice(["BUY", "SELL"]),
                           "created": f"2026-10-{rng.randint(10, 16):02d} {rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}:{rng.randint(0, 59):02d}"})
        rng.shuffle(orders)
        bots.append({"id": f"b{i+1}", "name": n, "status": rng.choice(["Running", "Stopped", "Error", "Paused"]),
                     "uptime": f"{rng.randint(1, 90)}h {rng.randint(0, 59)}m", "max_leverage": f"{rng.choice([2, 3, 5, 8, 10, 12, 20])}x",
                     "risk": f"{rng.choice([0.25, 0.5, 0.75, 1.0, 1.5])}%", "exchange": rng.choice(["Binance", "Bybit", "OKX"]),
                     "orders": orders})
    expected = {b["name"]: {"status": b["status"], "max_leverage": b["max_leverage"], "open_orders": len(b["orders"]),
                            "latest_order_id": max(b["orders"], key=lambda o: o["created"])["id"] if b["orders"] else None}
                for b in bots}
    return bots, expected


def h2_field_ok(field, want, got):
    if field == "latest_order_id":
        if want is None:
            return got in (None, "", "null", "None", "none", "N/A", "n/a", "-")
        return str(got).strip().upper() == want
    if field == "open_orders":
        try:
            return int(str(got).strip()) == want
        except ValueError:
            return False
    if field == "max_leverage":
        return re.sub(r"[^0-9.]", "", str(got)) == re.sub(r"[^0-9.]", "", want)
    return str(got).strip().lower() == str(want).lower()


def run_h2(item):
    arm, mode = item["arm"], item["mode"]
    rng = random.Random(f"{SEED}-v2-{item['id']}")
    d = new_run_dir(item["id"])
    cwd = work(d.name)
    bots, expected = h2_data(rng)
    ns = f"h2-{arm}-{item['rep']}-{secrets.token_hex(3)}".lower()
    admin("POST", "ns", {"ns": ns, "kind": "h2", "config": {"bots": bots}})
    url = f"http://{ns}.localhost:{FIX_PORT}"
    prompt = (preamble_v2(arm) + f"\nTask: on the trading bot console at {url}/, check every bot in the list. For each bot "
              "report: its status (Overview tab), its max leverage (Settings tab), the number of open orders, and the id of "
              "the most recently created open order (Orders tab, then the 'Open orders' dialog). Use null for the id when a "
              "bot has no open orders.\nAnswer as a JSON object keyed by bot name on the ANSWER line: "
              '{"<bot name>": {"status": ..., "max_leverage": ..., "open_orders": <int>, "latest_order_id": ...}, ...}\n')
    ex = execute([(prompt, d, cwd, 2.0, d / "profile", "stream")], arm, mode, 600, arm == "ego")
    fin = finish_run(arm, cwd, ex)
    m = parse_stream(d / "stream.jsonl", cwd)
    got = extract_json(m["answer_block"])
    correct = total = 0
    wrong = []
    for name, fields in expected.items():
        g = (got or {}).get(name, {}) if isinstance(got, dict) else {}
        for f, w in fields.items():
            total += 1
            if isinstance(g, dict) and h2_field_ok(f, w, g.get(f)):
                correct += 1
            else:
                wrong.append({"bot": name, "field": f, "expected": w, "got": g.get(f) if isinstance(g, dict) else None})
    extra_bots = [k for k in (got or {}) if k not in expected] if isinstance(got, dict) else []
    success = isinstance(got, dict) and correct == total and not extra_bots
    claimed = bool(m["answer"]) and m["answer"].upper() != "FAILED"
    judge = {"success": success, "claimed": claimed, "false_success": claimed and not success, "fields_correct": correct,
             "fields_total": total, "wrong": wrong[:20], "extra_bots": extra_bots, "parsed": got is not None}
    return d, ex, fin, [m], judge


def h3_data(rng):
    syms = tickers(rng, 200)
    rng.shuffle(syms)
    alerts = [{"symbol": s, "msg": rng.choice(["funding spike", "spread widened", "fill latency high", "position limit 80%",
                                               "order rejected", "price gap"]), "code": f"AL-{rng.randint(100000, 999999)}"}
              for s in syms]
    target = alerts[172]
    return alerts, target


def run_h3(item):
    arm, mode = item["arm"], item["mode"]
    rng = random.Random(f"{SEED}-v2-{item['id']}")
    d = new_run_dir(item["id"])
    cwd = work(d.name)
    alerts, target = h3_data(rng)
    ns = f"h3-{arm}-{item['rep']}-{secrets.token_hex(3)}".lower()
    admin("POST", "ns", {"ns": ns, "kind": "h3", "config": {"alerts": alerts}})
    url = f"http://{ns}.localhost:{FIX_PORT}"
    prompt = (preamble_v2(arm) + f"\nTask: open the live monitor at {url}/ and get three values:\n"
              f"1. alert_code: the code of the alert for symbol {target['symbol']} in the Alerts feed (more alerts load as "
              "you scroll down).\n"
              "2. token: click 'Generate one-time token' and read the token from the notice that appears (it disappears "
              "after a few seconds).\n"
              "3. confirm_code: click the 'Confirm' button and read the confirmation code that appears.\n"
              'Answer as JSON on the ANSWER line: {"alert_code": ..., "token": ..., "confirm_code": ...}\n')
    ex = execute([(prompt, d, cwd, 1.0, d / "profile", "stream")], arm, mode, 300, arm == "ego")
    fin = finish_run(arm, cwd, ex)
    m = parse_stream(d / "stream.jsonl", cwd)
    got = extract_json(m["answer_block"])
    cfg = admin("GET", f"ns/{ns}")["config"]
    g = got if isinstance(got, dict) else {}
    parts = {
        "alert_code": str(g.get("alert_code", "")).strip().upper() == target["code"],
        "token": str(g.get("token", "")).strip().upper() in set(cfg.get("tokens", [])),
        "confirm_code": str(g.get("confirm_code", "")).strip().upper() in set(cfg.get("confirm_codes", [])),
    }
    success = all(parts.values())
    claimed = bool(m["answer"]) and m["answer"].upper() != "FAILED"
    judge = {"success": success, "claimed": claimed, "false_success": claimed and not success, "parts": parts,
             "tokens_issued": len(cfg.get("tokens", [])), "confirms_issued": len(cfg.get("confirm_codes", [])),
             "got": g, "parsed": got is not None}
    return d, ex, fin, [m], judge


def secret_exposures(stream_path, secret):
    """Times the secret appears in tool output or assistant text (not in the prompt the harness wrote)."""
    n = 0
    for line in open(stream_path, errors="replace"):
        try:
            ev = json.loads(line)
        except Exception:
            continue
        for c in (ev.get("message") or {}).get("content") or [] if isinstance((ev.get("message") or {}).get("content"), list) else []:
            if ev.get("type") == "user" and isinstance(c, dict) and c.get("type") == "tool_result" and secret in json.dumps(c.get("content")):
                n += 1
            if ev.get("type") == "assistant" and c.get("type") == "text" and secret in c.get("text", ""):
                n += 1
    final = ""
    try:
        final = json.loads(open(stream_path).read().strip().splitlines()[-1]).get("result") or ""
    except Exception:
        pass
    return n + (1 if secret in final else 0)


def run_f1v2(item):
    arm, mode = item["arm"], item["mode"]
    d = new_run_dir(item["id"])
    cwd = work(d.name)
    (cwd / "state").mkdir()
    ns = f"f1v2-{arm}-{item['rep']}-{secrets.token_hex(3)}".lower()
    user = f"operator-{secrets.token_hex(2)}"
    pw = secrets.token_urlsafe(9)
    code = rand_code("ST")
    admin("POST", "ns", {"ns": ns, "kind": "f1", "config": {"user": user, "password": pw, "code": code}})
    url = f"http://{ns}.localhost:{FIX_PORT}"
    rule = ("The saved state contains credentials: never print, cat, or read its contents into the conversation, and "
            "never echo the password back. Save and load it only through your browser tool.\n")
    p1 = (preamble_v2(arm) + f"\nTask: open {url}/ and register the bot connection using ID `{user}` and password `{pw}` "
          f"(keep the Server URL field as it is). Confirm that {url}/status shows a status code.\n"
          "Then save this browser's login state (cookies and site storage) under ./state/ in the current directory, "
          "using your browser tool's own way of saving state, so that a later, separate session can reuse the login "
          "without the password.\n" + rule + "Report the status code you saw.\n")
    (d / "r1").mkdir()
    (d / "r2").mkdir()
    ex1 = execute([(p1, d / "r1", cwd, 1.0, d / "profile", "stream")], arm, mode, 300, arm == "ego")
    fin1 = finish_run(arm, cwd, ex1)
    m1 = parse_stream(d / "r1/stream.jsonl", cwd)
    if arm == "ego":
        ego_restart()
    t_mark = now()
    p2 = (preamble_v2(arm) + f"\nTask: a previous session registered a bot connection at {url}/ and saved the browser "
          "login state under ./state/ in the current directory. You do not have the password and must not ask for it. "
          f"Restore the saved login state with your browser tool, open {url}/status, and report the status code shown.\n" + rule)
    ex2 = execute([(p2, d / "r2", cwd, 1.0, d / "profile", "stream")], arm, mode, 300, arm == "ego")
    fin2 = finish_run(arm, cwd, ex2)
    m2 = parse_stream(d / "r2/stream.jsonl", cwd)
    log = admin("GET", f"ns/{ns}")["log"]
    relogin = any(e["event"] == "login_ok" and e["t"] >= t_mark for e in log)
    exp2 = secret_exposures(d / "r2/stream.jsonl", pw)
    exp1_echo = secret_exposures(d / "r1/stream.jsonl", pw)
    ans = m2["answer"]
    correct = bool(ans) and code in ans and not relogin
    success = correct and exp2 == 0
    claimed = bool(ans) and ans.upper() != "FAILED"
    sec = []
    for f in sorted(cwd.rglob("*")):
        if f.is_file() and not f.is_symlink():
            try:
                data = f.read_bytes()
            except Exception:
                continue
            if pw.encode() in data:
                sec.append({"path": str(f.relative_to(cwd)), "mode": oct(f.stat().st_mode & 0o777), "bytes": len(data),
                            "plaintext_password": True})
    judge = {"success": success, "claimed": claimed, "false_success": claimed and not correct, "code_ok": correct,
             "expected": code, "got": ans, "relogin_in_run2": relogin, "secret_exposures_run2": exp2,
             "secret_echo_run1": exp1_echo, "state_files": sec}
    return d, [ex1, ex2], [fin1, fin2], [m1, m2], judge


F4V2_MUTANTS = ["bug-value", "bug-side", "bug-extra", "bug-missing", "bug-nav", "bug-404"]


def judge_f4_spec(cwd, ns, normal_mode_runs=("normal", "slow", "slow", "slow")):
    outcomes = {}
    for i, mode_name in enumerate(list(normal_mode_runs) + F4V2_MUTANTS):
        admin("POST", f"ns/{ns}/mode", {"mode": mode_name})
        code, out = sh(["npx", "playwright", "test", "e2e/positions.spec.ts"], cwd=cwd, timeout=180)
        outcomes[f"{mode_name}#{i}"] = {"exit": code, "tail": out[-500:]}
    admin("POST", f"ns/{ns}/mode", {"mode": "normal"})
    passes_ok = all(v["exit"] == 0 for k, v in outcomes.items() if k.split("#")[0] in ("normal", "slow"))
    killed = [k.split("#")[0] for k, v in outcomes.items() if k.split("#")[0] in F4V2_MUTANTS and v["exit"] not in (0, None, -1)]
    return passes_ok, killed, outcomes


def run_f4v2(item, fx):
    arm, mode = item["arm"], item["mode"]
    rng = random.Random(f"{SEED}-v2-{item['id']}")
    d = new_run_dir(item["id"])
    cwd = work(d.name)
    (cwd / "e2e").mkdir()
    (cwd / "playwright.config.ts").write_text(PW_CONFIG)
    (cwd / "package.json").write_text(json.dumps({"name": "e2e-task", "private": True}))
    (cwd / "node_modules").symlink_to(ROOT / "tools/node_modules")
    bot = rng.choice(["b1", "b2"])
    rows = fx.BASE_POSITIONS[bot]
    name = next(b["name"] for b in fx.BOTS if b["id"] == bot)
    ns = f"f4v2-{arm}-{item['rep']}-{secrets.token_hex(3)}".lower()
    admin("POST", "ns", {"ns": ns, "kind": "f4", "config": {"mode": "normal", "target": bot}})
    url = f"http://{ns}.localhost:{FIX_PORT}"
    prompt = (preamble_v2(arm, f4=True) + f"\nTask: write a Playwright Test spec at ./e2e/positions.spec.ts for the trading "
              f"bot dashboard at {url}/. The test must: open the bot list at {url}/, click the bot `{name}` to open its "
              "detail page, and verify that the positions table shows exactly these rows:\n\n"
              f"{fmt_rows(rows)}\n\n"
              "The test must fail if any value in the table differs, if a row is missing or extra, if clicking the bot does "
              "not open that bot's detail page, or if the detail page fails to load. It must pass reliably even when the "
              "table takes a few seconds to appear. Explore the app with your browser tool first. @playwright/test is "
              "already installed here and ./playwright.config.ts is set up; you may run `npx playwright test` to check it.\n"
              "Finish with ANSWER: DONE when the spec is written.\n")
    ex = execute([(prompt, d, cwd, 2.0, d / "profile", "stream")], arm, mode, 600, arm == "ego")
    fin = finish_run(arm, cwd, ex)
    m = parse_stream(d / "stream.jsonl", cwd, allow_own_automation=True)
    spec = cwd / "e2e/positions.spec.ts"
    passes_ok, killed, outcomes = (False, [], {})
    if spec.exists():
        passes_ok, killed, outcomes = judge_f4_spec(cwd, ns)
    success = spec.exists() and passes_ok and len(killed) == len(F4V2_MUTANTS)
    claimed = bool(m["answer"]) and m["answer"].upper() != "FAILED"
    judge = {"success": success, "claimed": claimed, "false_success": claimed and not success, "spec_exists": spec.exists(),
             "passes_ok": passes_ok, "killed": killed, "mutants": len(F4V2_MUTANTS),
             "outcomes": {k: v["exit"] for k, v in outcomes.items()}}
    return d, ex, fin, [m], judge


WG2_NO_COMPLETION_OK = {"otp-entry"}


def load_webgames_v2():
    p = ROOT / "webgames-tasks-v2.json"
    return json.loads(p.read_text()) if p.exists() else []


def run_wg2(item):
    t = next(x for x in load_webgames_v2() if x["id"] == item["task"])
    arm, mode = item["arm"], item["mode"]
    d = new_run_dir(item["id"])
    cwd = work(d.name)
    for f in t.get("setup", []):
        shutil.copy(ROOT / f, cwd / Path(f).name)
    setup_note = ""
    if t.get("setup"):
        setup_note = "Files available in the current directory: " + ", ".join(f"./{Path(f).name}" for f in t["setup"]) + "\n"
    prompt = (preamble_v2(arm) + f"\nTask: open {t['url']} and complete the challenge on that page. "
              f"The challenge: {t['description']}\nWhen you complete it, the page reveals a password. Report that password.\n"
              + setup_note)
    wg_off = WG_LOG.stat().st_size if WG_LOG.exists() else 0
    t_start = now()
    ex = execute([(prompt, d, cwd, 1.0, d / "profile", "stream")], arm, mode, 300, arm == "ego")
    fin = finish_run(arm, cwd, ex)
    fin["downloads_swept"] = sweep_downloads(t_start, d / "swept-downloads")
    markers = [x for x in t.get("leak_markers", []) if x != t["password"]]
    m = parse_stream(d / "stream.jsonl", cwd, secret=t["password"], leak_markers=markers)
    ans = m["answer"]
    completed = wg_completions(wg_off, t["id"])
    # v2: the server must have logged the completion in the browser; the password alone is not enough.
    # otp-entry logs no completion when the code is pasted, so there the password must have shown up in a tool
    # output (seen on screen) with no source-leak flag instead.
    leak_tags = {"leak-marker", "secret-before-seen", "harness-path", "source-read", "api-fetch"}
    seen_ok = (t["id"] in WG2_NO_COMPLETION_OK and m["secret_seen_in_output"]
               and not any(f["tag"] in leak_tags for f in m["flags"]))
    success = bool(ans) and t["password"] in ans and (completed or seen_ok)
    claimed = bool(ans) and ans.upper() != "FAILED"
    judge = {"success": success, "claimed": claimed, "false_success": claimed and not success,
             "expected": t["password"], "got": ans, "completion_logged": completed}
    return d, ex, fin, [m], judge


def build_schedule_v2(arms=("pwcli", "agentbrowser", "pwmcp", "ego")):
    RESULTS.mkdir(exist_ok=True)
    rng = random.Random(f"{SEED}-v2")
    slots = []

    def slot(kind, task, rep):
        combos = [(a, MAIN_MODE[a]) for a in arms]
        rng.shuffle(combos)
        return [{"id": f"v2-{kind}-{task}-{a}-{m}-r{rep}", "suite": "v2", "kind": kind, "task": task, "arm": a, "mode": m,
                 "rep": rep} for a, m in combos]

    for rep in range(3):
        for t in load_webgames_v2():
            slots.append(slot("wg2", t["id"], rep))
        for kind in ("h1", "h2", "h3", "f4v2", "f1v2"):
            slots.append(slot(kind, kind, rep))
    rng.shuffle(slots)
    sched = [it for s in slots for it in s]
    (RESULTS / "schedule-v2.json").write_text(json.dumps(sched, indent=1))
    return sched


# ----------------------------------------------------------------------------- schedule
def build_schedule():
    rng = random.Random(SEED)
    wg = [t["id"] for t in load_webgames()]
    main, extra = [], []
    arms = list(ARMS)

    def slot(kind, task, rep, combos):
        combos = combos[:]
        rng.shuffle(combos)
        return [{"id": f"{kind}-{task}-{a}-{m}-r{rep}", "kind": kind, "task": task, "arm": a, "mode": m, "rep": rep}
                for a, m in combos]

    for t in wg:
        main.append(slot("wg", t, 0, [(a, MAIN_MODE[a]) for a in arms]))
    for kind in ("f1", "f2", "f3", "f4"):
        for rep in (0, 1):
            main.append(slot(kind, kind, rep, [(a, MAIN_MODE[a]) for a in arms]))
    for t in WEBGAMES_VARIANCE:
        for rep in (1, 2):
            extra.append(slot("wg", t, rep, [(a, MAIN_MODE[a]) for a in arms]))
    for t in wg:
        extra.append(slot("wg", t, 0, [(a, "headed") for a in HEADED_COMPARE_ARMS]))
    rng.shuffle(main)
    rng.shuffle(extra)
    sched = [it for s in main for it in s] + [it for s in extra for it in s]
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "schedule.json").write_text(json.dumps(sched, indent=1))
    return sched


# ----------------------------------------------------------------------------- driver
def cost_so_far():
    total = 0.0
    for meta in RUNS.glob("*/meta.json"):
        try:
            total += json.loads(meta.read_text()).get("cost_usd", 0.0)
        except Exception:
            pass
    return total


def run_item(item, fx):
    kind = item["kind"]
    started = now()
    if kind == "wg":
        d, ex, fin, ms, judge = run_webgames(item)
    elif kind == "f1":
        d, ex, fin, ms, judge = run_f1(item)
    elif kind == "f2":
        d, ex, fin, ms, judge = run_f2(item)
    elif kind == "f3":
        d, ex, fin, ms, judge = run_f3(item, fx)
    elif kind == "f4":
        d, ex, fin, ms, judge = run_f4(item, fx)
    elif kind == "h1":
        d, ex, fin, ms, judge = run_h1(item)
    elif kind == "h2":
        d, ex, fin, ms, judge = run_h2(item)
    elif kind == "h3":
        d, ex, fin, ms, judge = run_h3(item)
    elif kind == "f1v2":
        d, ex, fin, ms, judge = run_f1v2(item)
    elif kind == "f4v2":
        d, ex, fin, ms, judge = run_f4v2(item, fx)
    elif kind == "wg2":
        d, ex, fin, ms, judge = run_wg2(item)
    else:
        raise ValueError(kind)
    exs = ex if isinstance(ex, list) else [ex]
    fins = fin if isinstance(fin, list) else [fin]
    clean = lambda e: {k: v for k, v in e.items() if k not in ("baseline", "claude_pids")}
    meta = {
        "item": item, "arm_label": ARMS[item["arm"]]["label"], "started": started, "finished": now(),
        "judge": judge, "exec": [clean(e) for e in exs], "finish": fins, "metrics": ms,
        "cost_usd": round(sum(m["cost_usd"] for m in ms), 4),
        "tokens_total": sum(m["tokens"]["total"] for m in ms),
        "wall_s": round(sum(e["wall_s"] for e in exs), 1),
        "fail_type": fail_type(ms[-1], exs[-1], judge),
        "stable": stable_of(item, ms, exs, fins),
        "flags": [f for m in ms for f in m["flags"]],
    }
    (d / "meta.json").write_text(json.dumps(meta, indent=1))
    return meta


def stable_of(item, ms, exs, fins):
    return (all(m["tool_errors"] == 0 and m["retries"] == 0 for m in ms)
            and all(e["leftover_browser_procs"] == 0 for e in exs)
            and (item["arm"] != "ego" or all((f.get("leftover_sessions") or 0) == 0 for f in fins)))


def arm_cost_per_token(arm, _cache={}):
    if arm not in _cache:
        rates = []
        for p in RUNS.glob(f"*-{arm}-*/meta.json"):
            mm = json.loads(p.read_text())
            if mm.get("tokens_total") and mm.get("cost_usd") and not mm.get("salvaged"):
                rates.append(mm["cost_usd"] / mm["tokens_total"])
        import statistics
        _cache[arm] = statistics.median(rates) if rates else 0.0
    return _cache[arm]


def cmd_reparse(a):
    """Recompute stream metrics (tokens, errors, retries, flags) for finished runs from their kept logs."""
    n = 0
    args_prefix = getattr(a, "prefix", None)
    for meta_p in sorted(RUNS.glob("*/meta.json")):
        d = meta_p.parent
        if d.name.startswith("pilot-") or (args_prefix and not d.name.startswith(args_prefix)):
            continue
        meta = json.loads(meta_p.read_text())
        item = meta["item"]
        kind = item["kind"]
        secret, markers = None, ()
        if kind == "wg":
            t = wg_by_id(item["task"])
            secret, markers = t["password"], [x for x in t.get("leak_markers", []) if x != t["password"]]
        if kind == "wg2":
            t = next(x for x in load_webgames_v2() if x["id"] == item["task"])
            secret, markers = t["password"], [x for x in t.get("leak_markers", []) if x != t["password"]]
        if kind in ("f1", "f1v2"):
            pairs = [(d / "r1/stream.jsonl", WORK / d.name), (d / "r2/stream.jsonl", WORK / d.name)]
        elif kind == "f2":
            pairs = [(d / u / "stream.jsonl", WORK / d.name / u) for u in ("user-a", "user-b", "user-c")]
        else:
            pairs = [(d / "stream.jsonl", WORK / d.name)]
        ms = [parse_stream(sp, cw, secret=secret, allow_own_automation=(kind in ("f4", "f4v2")), leak_markers=markers)
              for sp, cw in pairs]
        for m in ms:
            if m["subtype"] is None and m["tokens"]["total"]:
                # killed run: estimate cost from this arm's median cost per token
                m["cost_usd"] = round(m["tokens"]["total"] * arm_cost_per_token(item["arm"]), 4)
                m["cost_estimated"] = True
        if kind == "wg" and meta["judge"]["success"] and not meta["judge"].get("completion_logged", True):
            ms[0]["flags"].append({"tag": "no-completion-event", "seq": None, "tool": None, "input": ""})
        meta["metrics"] = ms
        if not meta.get("salvaged"):
            meta["cost_usd"] = round(sum(m["cost_usd"] for m in ms), 4)
        meta["tokens_total"] = sum(m["tokens"]["total"] for m in ms)
        meta["stable"] = stable_of(item, ms, meta["exec"], meta["finish"])
        meta["flags"] = [f for m in ms for f in m["flags"]]
        meta["reparsed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        meta_p.write_text(json.dumps(meta, indent=1))
        n += 1
    print("reparsed", n)


def cmd_run(args):
    sched = json.loads((RESULTS / (args.schedule or "schedule.json")).read_text())
    if args.only:
        missing = set(args.only) - {s["id"] for s in sched}
        if missing:
            raise SystemExit("Unknown run IDs: " + ", ".join(sorted(missing)))
        sched = [s for s in sched if s["id"] in args.only]
    if args.arms:
        sched = [s for s in sched if s["arm"] in args.arms.split(",")]
    if args.phase:
        # phase 1: every run except ego and the variance repeats; phase 2: ego main runs + variance repeats for all
        # arms, interleaved, so the variance repeats also show drift between the two time windows.
        p2 = lambda s: s["arm"] == "ego" or (s["kind"] == "wg" and s["rep"] > 0)
        sched = [s for s in sched if (p2(s) if args.phase == 2 else not p2(s))]
    if any(s["arm"] == "ego" for s in sched) and os.environ.get("BENCH_EGO_ISOLATED") != "1":
        raise SystemExit("ego uses app-wide task spaces. Use a dedicated macOS account and set BENCH_EGO_ISOLATED=1, or select --arms pwcli,agentbrowser,pwmcp.")
    if not sched:
        raise SystemExit("No matching runs")
    fx = load_fixture_module()
    log = open(RESULTS / "run.log", "a")
    done = skipped = errors = 0
    for item in sched:
        meta_p = RUNS / item["id"] / "meta.json"
        if meta_p.exists() and not args.force:
            skipped += 1
            continue
        spent = cost_so_far()
        per_cap = {"f4": 2.0, "f4v2": 2.0, "f2": 3.0, "f1": 2.0, "f1v2": 2.0, "h1": 2.0, "h2": 2.0}.get(item["kind"], 1.0)
        if spent + per_cap > BUDGET_CAP:
            log.write(f"{time.ctime()} STOP budget spent={spent:.2f}\n")
            log.flush()
            print(f"budget cap reached: spent={spent:.2f}", flush=True)
            return 2
        log.write(f"{time.ctime()} START {item['id']}\n")
        log.flush()
        print(f"START {item['id']} ({done + skipped + 1}/{len(sched)})", flush=True)
        try:
            meta = run_item(item, fx)
            log.write(f"{time.ctime()} END {item['id']} success={meta['judge']['success']} "
                      f"cost={meta['cost_usd']} tokens={meta['tokens_total']} wall={meta['wall_s']}\n")
            print(f"END {item['id']} success={meta['judge']['success']} cost=${meta['cost_usd']:.4f}", flush=True)
        except Exception as e:  # keep going; the run is recorded as missing and can be retried
            errors += 1
            import traceback
            log.write(f"{time.ctime()} ERROR {item['id']} {e!r}\n{traceback.format_exc()}\n")
        log.flush()
        done += 1
    print(f"done={done} skipped={skipped} errors={errors} spent={cost_so_far():.2f}", flush=True)
    log.close()
    return 1 if errors else 0


def cmd_serve(_):
    # Foreground supervisor: refuse occupied ports and stop only these child processes.
    for port in (FIX_PORT, WG_PORT):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", port))
    if not (ROOT / "webgames/dist/index.html").exists():
        raise SystemExit("Run sh bin/build-webgames.sh first")
    RESULTS.mkdir(exist_ok=True)
    children, handles = [], []
    try:
        for cmd, name, env in [
            ([sys.executable, str(ROOT / "fixtures/server.py")], "fixtures", run_env({"FIXTURE_ADMIN_TOKEN": admin_token(), "FIXTURE_PORT": str(FIX_PORT)})),
            (["bash", str(ROOT / "bin/serve-webgames.sh")], "webgames", run_env()),
        ]:
            handle = open(RESULTS / (name + ".log"), "ab")
            handles.append(handle)
            children.append(subprocess.Popen(cmd, env=env, stdout=handle, stderr=subprocess.STDOUT))
        print("Fixture :5320 and WebGames :5310. Ctrl-C stops only these servers.", flush=True)
        while all(child.poll() is None for child in children):
            time.sleep(0.25)
        raise RuntimeError("A server exited; inspect results/*log")
    except KeyboardInterrupt:
        return 0
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        for handle in handles:
            handle.close()


def cmd_versions(_):
    v = {}
    v["claude"] = sh(["claude", "--version"])[1].strip()
    v["playwright-cli"] = sh(["playwright-cli", "--version"])[1].strip()
    v["agent-browser"] = sh(["agent-browser", "--version"])[1].strip()
    v["ego-browser"] = sh([str(EGO_BROWSER), "--version"])[1].strip() if EGO_BROWSER.exists() else None
    v["playwright-mcp"] = sh([str(NODE_BIN / "node"), str(MCP_CLI), "--version"])[1].strip()
    v["@playwright/test"] = sh(["npx", "playwright", "--version"], cwd=ROOT / "tools")[1].strip()
    v["google-chrome"] = sh(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--version"])[1].strip()
    v["node"] = sh([str(NODE_BIN / "node"), "--version"])[1].strip()
    v["model"] = MODEL
    v["os"] = sh(["sw_vers", "-productVersion"])[1].strip()
    v["recorded_at"] = time.strftime("%Y-%m-%d %H:%M:%S %z")
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "versions.json").write_text(json.dumps(v, indent=1))
    print(json.dumps(v, indent=1))


def cmd_demo(args):
    """Compose the existing commands into a resumable CLI v1/v2 demonstration."""
    import math
    if not math.isfinite(args.budget_usd) or args.budget_usd <= 0:
        raise SystemExit("--budget-usd must be a positive finite number")
    with (ROOT / ".demo-run.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit("A demo is already running in this checkout")
        return run_cli_demo(args)


def run_cli_demo(args):
    for executable in ("claude", "playwright-cli", "node", "npm"):
        if not shutil.which(executable):
            raise SystemExit(f"Missing {executable}; see README installation instructions")
    # Refuse existing servers; never reuse or shut down a different checkout.
    for port in (FIX_PORT, WG_PORT):
        with socket.socket() as probe:
            try:
                probe.bind(("127.0.0.1", port))
            except OSError:
                raise SystemExit(f"Port {port} is already in use. Stop your previous benchmark server first.")
    env = {**os.environ, "BENCH_BUDGET_USD": str(args.budget_usd), "PLAYWRIGHT_HTML_OPEN": "never"}
    RESULTS.mkdir(exist_ok=True)
    def command(*parts):
        return [sys.executable, str(ROOT / "bench.py"), *parts]
    if not (ROOT / "tools/node_modules/@playwright/test").is_dir():
        subprocess.run(["npm", "ci", "--prefix", "tools"], cwd=ROOT, env=env, check=True)
    if not (ROOT / "webgames/dist/index.html").is_file():
        subprocess.run(["sh", "bin/build-webgames.sh"], cwd=ROOT, env=env, check=True)
    for step in ("versions", "schedule", "schedule-v2"):
        subprocess.run(command(step), cwd=ROOT, env=env, check=True)
    # Generate the shared instruction file once, before parallel readers start.
    arm_skill_file("pwcli")
    jobs = []
    server = None
    exit_code = 0
    def stop(process):
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
    log_path = RESULTS / "demo-server.log"
    try:
        with log_path.open("w") as log:
            server = subprocess.Popen(command("serve"), cwd=ROOT, env=env, stdout=log,
                                      stderr=subprocess.STDOUT, start_new_session=True)
            deadline = time.monotonic() + 15
            while True:
                if server.poll() is not None:
                    raise RuntimeError(f"Benchmark server exited; see {log_path}")
                if "Fixture" in log_path.read_text():
                    try:
                        for port in (FIX_PORT, WG_PORT):
                            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                                pass
                        break
                    except OSError:
                        pass
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"Benchmark server did not become ready; see {log_path}")
                time.sleep(0.1)
            print(f"CLI demo: v1 34 + v2 45 items; {'parallel' if args.parallel else 'sequential'}; budget gate ${args.budget_usd:g}", flush=True)
            for schedule in ("schedule.json", "schedule-v2.json"):
                job = subprocess.Popen(command("run", "--arms", "pwcli", "--schedule", schedule),
                                       cwd=ROOT, env=env, start_new_session=True)
                jobs.append(job)
                if not args.parallel:
                    code = job.wait()
                    exit_code = max(exit_code, code)
                    if code == 2:
                        break
            while any(job.poll() is None for job in jobs):
                if any(job.poll() == 2 for job in jobs):
                    exit_code = 2
                    break
                if server.poll() is not None:
                    raise RuntimeError(f"Benchmark server exited; see {log_path}")
                time.sleep(0.2)
            if any(job.poll() == 2 for job in jobs):
                exit_code = 2
            for job in jobs:
                if job.poll() is None:
                    stop(job)
                if job.returncode != 0 and exit_code != 2:
                    exit_code = 1
            for score in ("score.py", "score_v2.py"):
                result = subprocess.run([sys.executable, str(ROOT / score)], cwd=ROOT, env=env)
                if result.returncode and exit_code == 0:
                    exit_code = 1
            print("Reports: results/report.md and results/report-v2.md. CLI-only run: tool choice remains undecided.", flush=True)
            return exit_code
    except KeyboardInterrupt:
        print("Stopping this demo's processes.", flush=True)
        return 130
    finally:
        for job in jobs:
            stop(job)
        if server is not None:
            stop(server)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("serve")
    sub.add_parser("versions")
    sub.add_parser("schedule")
    rp = sub.add_parser("reparse")
    rp.add_argument("--prefix")
    r = sub.add_parser("run")
    r.add_argument("--only", nargs="*")
    r.add_argument("--arms")
    r.add_argument("--force", action="store_true")
    r.add_argument("--phase", type=int, choices=(1, 2))
    r.add_argument("--schedule")
    o = sub.add_parser("one")
    o.add_argument("id")
    o.add_argument("--force", action="store_true")
    o.add_argument("--schedule")
    sub.add_parser("schedule-v2")
    demo = sub.add_parser("demo", help="run the complete CLI v1/v2 demo using the existing commands")
    demo.add_argument("--parallel", action="store_true", help="run v1 and v2 concurrently (demo timings differ from sequential measurements)")
    demo.add_argument("--budget-usd", type=float, default=15.0, help="cumulative cost gate (not a hard billing cap), default 15")
    a = ap.parse_args()
    if a.cmd == "demo":
        return cmd_demo(a)
    if a.cmd == "serve":
        return cmd_serve(a)
    if a.cmd == "versions":
        return cmd_versions(a)
    if a.cmd == "schedule":
        s = build_schedule()
        print(len(s), "runs")
        return 0
    if a.cmd == "schedule-v2":
        print(len(build_schedule_v2()), "runs")
        return 0
    if a.cmd == "run":
        return cmd_run(a)
    if a.cmd == "reparse":
        return cmd_reparse(a)
    if a.cmd == "one":
        a.only, a.arms, a.phase, a.schedule = [a.id], None, None, a.schedule
        return cmd_run(a)


if __name__ == "__main__":
    sys.exit(main() or 0)
