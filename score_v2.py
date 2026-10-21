#!/usr/bin/env python3
"""Q6 v2 score table (harder tasks). Rules were fixed in the Work Brief before the v2 runs (2026-10-16).

Same weights as v1 (quality 50 / tokens 25 / speed 15 / stability 10) and the same decision rules, with:
  - gates: F1v2 3/3 (correct code, no re-login, no password in the transcript) and v1 F2 2/2
  - quality: success rate over wg2 + h1 + h2 + h3 + f4v2 (3 reps each), reported with a Wilson 95% interval
  - speed: median tool time (wall minus model API time); within the noise band of the best counts as best
  - success-difference rule scaled to the run count: ceil(3/14 * N) more successes
Writes results/summary-v2.json and results/report-v2.md.
"""
import json
import math
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUNS, RESULTS = ROOT / "runs", ROOT / "results"
ARM_ORDER = ["pwcli", "agentbrowser", "ego", "pwmcp"]
LABEL = {"pwcli": "Playwright CLI", "agentbrowser": "agent-browser", "ego": "ego lite", "pwmcp": "Playwright MCP"}
CANDIDATES = ["agentbrowser", "ego"]
QUALITY_KINDS = ("wg2", "h1", "h2", "h3", "f4v2")
W = {"quality": 0.50, "tokens": 0.25, "speed": 0.15, "stability": 0.10}


def med(xs):
    return st.median(xs) if xs else None


def rel_spread(xs):
    m = med(xs)
    return (max(xs) - min(xs)) / m if xs and m else 0.0


def wilson(k, n, z=1.96):
    if not n:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def tool_time(m):
    return sum(max(0.0, ((x.get("duration_ms") or 0) - (x.get("duration_api_ms") or 0)) / 1000) for x in m["metrics"])


def load():
    out = []
    for p in sorted(RUNS.glob("v2-*/meta.json")):
        m = json.loads(p.read_text())
        # duration_api_ms is not copied into metrics by parse_stream; read it from the stream tail.
        for i, x in enumerate(m["metrics"]):
            if "duration_api_ms" not in x:
                d = p.parent
                streams = {"f1v2": [d / "r1/stream.jsonl", d / "r2/stream.jsonl"]}.get(m["item"]["kind"], [d / "stream.jsonl"])
                try:
                    last = json.loads(streams[i].read_text().strip().splitlines()[-1])
                    x["duration_api_ms"] = last.get("duration_api_ms")
                    x["duration_ms"] = last.get("duration_ms")
                except Exception:
                    x["duration_api_ms"] = x["duration_ms"] = None
        if m["item"]["arm"] == "ego":
            fix_ego_leftover(m)
        out.append(m)
    return out


def fix_ego_leftover(m):
    """The harness drops ego app processes from the baseline (so ego memory counts toward the run), which made the
    always-running ego app itself (`ego lite --startup-ego-browser-service`) count as one leftover browser in every
    ego run (122/122 execs = 1). Subtract it; ego cleanup is judged by leftover task spaces (`leftover_sessions`)."""
    for e in m["exec"]:
        e["leftover_browser_procs_raw"] = e["leftover_browser_procs"]
        e["leftover_browser_procs"] = max(0, e["leftover_browser_procs"] - 1)
    m["stable"] = (all(x["tool_errors"] == 0 and x["retries"] == 0 for x in m["metrics"])
                   and all(e["leftover_browser_procs"] == 0 for e in m["exec"])
                   and all((f.get("leftover_sessions") or 0) == 0 for f in m["finish"]))


def f2_gate_v1():
    g = {}
    for p in RUNS.glob("f2-f2-*/meta.json"):
        m = json.loads(p.read_text())
        a = m["item"]["arm"]
        g.setdefault(a, [0, 0])
        g[a][1] += 1
        g[a][0] += 1 if m["judge"]["success"] else 0
    return g


def apply_violations(metas):
    """Runs a reviewer confirmed as breaking the task rules (results/violations-v2.json: {run_id: reason}) fail."""
    p = RESULTS / "violations-v2.json"
    v = json.loads(p.read_text()) if p.exists() else {}
    for m in metas:
        if m["item"]["id"] in v and m["judge"]["success"]:
            m["judge"]["success"] = False
            m["judge"]["violation"] = v[m["item"]["id"]]
            m["fail_type"] = "rule-violation"
    return v


def main():
    metas = load()
    violations = apply_violations(metas)
    f2 = f2_gate_v1()
    by = {}
    for m in metas:
        by.setdefault(m["item"]["arm"], []).append(m)
    arms = [a for a in ARM_ORDER if a in by]
    S = {}
    for a in arms:
        runs = by[a]
        q = [m for m in runs if m["item"]["kind"] in QUALITY_KINDS]
        f1 = [m for m in runs if m["item"]["kind"] == "f1v2"]
        succ = sum(1 for m in q if m["judge"]["success"])
        lo, hi = wilson(succ, len(q))
        per_task = {}
        for m in q:
            per_task.setdefault((m["item"]["kind"], m["item"]["task"]), []).append(m)
        f2p, f2n = f2.get(a, [0, 0])
        S[a] = {
            "label": LABEL[a], "n_quality_runs": len(q), "successes": succ, "ci95": [round(lo, 3), round(hi, 3)],
            "f1_pass": sum(1 for m in f1 if m["judge"]["success"]), "f1_n": len(f1),
            "f1_code_ok": sum(1 for m in f1 if m["judge"].get("code_ok")),
            "f1_exposed_runs": sum(1 for m in f1 if m["judge"].get("secret_exposures_run2", 0) > 0),
            "f1_echo_run1": sum(1 for m in f1 if m["judge"].get("secret_echo_run1", 0) > 0),
            "f2_pass": f2p, "f2_n": f2n,
            "false_success": sum(1 for m in runs if m["judge"].get("false_success")),
            "tokens_per_success": (sum(m["tokens_total"] for m in q) / succ) if succ else None,
            "median_tokens": med([m["tokens_total"] for m in q]),
            "median_tool_s": med([tool_time(m) for m in q]),
            "median_wall_s": med([m["wall_s"] for m in q]),
            # reference only (not scored): failures that burn minutes show up here, not in the median
            "wall_per_success": (sum(m["wall_s"] for m in q) / succ) if succ else None,
            "max_context_max": max([x["tokens"]["max_context"] for m in q for x in m["metrics"]] or [0]),
            "max_context_median": med([max(x["tokens"]["max_context"] for x in m["metrics"]) for m in q]),
            "stable_share": (sum(1 for m in runs if m["stable"]) / len(runs)) if runs else 0,
            "tool_errors": sum(x["tool_errors"] for m in runs for x in m["metrics"]),
            "retries": sum(x["retries"] for m in runs for x in m["metrics"]),
            "leftover_runs": sum(1 for m in runs if any(e["leftover_browser_procs"] for e in m["exec"])),
            "cost_usd": round(sum(m["cost_usd"] for m in runs), 3),
            "by_kind": {},
            "flags": sorted({(m["item"]["id"], f["tag"]) for m in runs for f in m["flags"]}),
            "state_files": [f for m in f1 for f in m["judge"].get("state_files", [])],
        }
        for kind in QUALITY_KINDS:
            ks = [m for m in q if m["item"]["kind"] == kind]
            if ks:
                S[a]["by_kind"][kind] = {"success": sum(1 for m in ks if m["judge"]["success"]), "n": len(ks),
                                         "median_tokens": med([m["tokens_total"] for m in ks]),
                                         "median_max_context": med([max(x["tokens"]["max_context"] for x in m["metrics"]) for m in ks]),
                                         "median_tool_s": med([tool_time(m) for m in ks])}
        S[a]["noise"] = {
            "token_rel": med([rel_spread([m["tokens_total"] for m in v]) for v in per_task.values() if len(v) >= 2]) or 0.0,
            "time_rel": med([rel_spread([tool_time(m) for m in v]) for v in per_task.values() if len(v) >= 2]) or 0.0,
            "flip_tasks": sum(1 for v in per_task.values() if len({m["judge"]["success"] for m in v}) > 1),
            "n_tasks": len(per_task),
        }
        S[a]["gate_pass"] = (S[a]["f1_n"] >= 3 and S[a]["f1_pass"] == S[a]["f1_n"] and f2n >= 2 and f2p == f2n)

    tps = [S[a]["tokens_per_success"] for a in arms if S[a]["tokens_per_success"]]
    tts = [S[a]["median_tool_s"] for a in arms if S[a]["median_tool_s"]]
    best_t = min(tts) if tts else None
    for a in arms:
        s = S[a]
        n = s["n_quality_runs"] or 1
        band = max(S[x]["noise"]["time_rel"] for x in arms)
        if s["median_tool_s"] and best_t and (s["median_tool_s"] - best_t) / best_t <= band:
            speed = 100.0
        else:
            speed = round(100 * best_t / s["median_tool_s"], 1) if s["median_tool_s"] else 0.0
        s["score"] = {"quality": round(100 * s["successes"] / n, 1),
                      "tokens": round(100 * min(tps) / s["tokens_per_success"], 1) if s["tokens_per_success"] else 0.0,
                      "speed": speed, "stability": round(100 * s["stable_share"], 1)}
        s["score"]["composite"] = round(sum(W[k] * s["score"][k] for k in W), 1)
        nz = s["noise"]
        s["noise_band_points"] = round(50 * nz["flip_tasks"] / max(1, nz["n_tasks"]) + 25 * nz["token_rel"] + 15 * nz["time_rel"], 1)

    decision = {"notes": []}
    pw = S.get("pwcli")
    if pw and not pw["gate_pass"]:
        decision["notes"].append(f"Playwright CLI가 필수 조건에서 떨어졌다(F1v2 {pw['f1_pass']}/{pw['f1_n']}, F2 {pw['f2_pass']}/{pw['f2_n']}). 원인을 확인한 뒤 다시 판정한다(규칙 5).")
    for a in CANDIDATES:
        if a not in S or not pw:
            continue
        s = S[a]
        if not s["gate_pass"]:
            decision["notes"].append(f"{s['label']}: 필수 조건 탈락(F1v2 {s['f1_pass']}/{s['f1_n']}, F2 {s['f2_pass']}/{s['f2_n']}).")
            continue
        if s["false_success"] > pw["false_success"]:
            decision["notes"].append(f"{s['label']}: 거짓 성공 {s['false_success']}건 > Playwright CLI {pw['false_success']}건, 전환 후보 제외(규칙 3).")
            continue
        need = math.ceil(3 / 14 * s["n_quality_runs"])
        diff = s["successes"] - pw["successes"]
        why = []
        if diff >= need and diff > max(s["noise"]["flip_tasks"], pw["noise"]["flip_tasks"]):
            why.append(f"성공 {diff}개 더 많음(기준 {need})")
        if s["successes"] >= pw["successes"]:
            tg = 1 - s["median_tokens"] / pw["median_tokens"] if pw["median_tokens"] else 0
            ttg = 1 - s["median_tool_s"] / pw["median_tool_s"] if pw["median_tool_s"] else 0
            if tg >= 0.40 and tg > max(s["noise"]["token_rel"], pw["noise"]["token_rel"]):
                why.append(f"중앙값 토큰 {tg:.0%} 적음")
            if ttg >= 0.40 and ttg > max(s["noise"]["time_rel"], pw["noise"]["time_rel"]):
                why.append(f"중앙값 도구 시간 {ttg:.0%} 짧음")
        if why:
            decision.setdefault("switch_candidates", []).append(a)
            decision["notes"].append(f"{s['label']}: 전환 조건 충족({', '.join(why)}). 전환을 제안한다.")
        else:
            decision["notes"].append(f"{s['label']}: 필수 조건 통과, 전환 조건 미달(성공 차 {diff:+d}, 기준 +{need}).")
    for a in arms:
        if S[a]["leftover_runs"]:
            decision["notes"].append(f"{S[a]['label']}: 닫으라는 지시에도 브라우저가 남은 실행 {S[a]['leftover_runs']}건(규칙 6).")
    decision["verdict"] = ("Playwright CLI 유지" if not decision.get("switch_candidates")
                           else "전환 제안: " + ", ".join(LABEL[a] for a in decision["switch_candidates"]))

    complete = (len(arms) >= 2 and "pwcli" in S and all(
        S[a]["n_quality_runs"] >= 42 and S[a]["f1_n"] >= 3 and S[a]["f2_n"] >= 2
        for a in arms))
    if not complete:
        decision = {"verdict": "실험 미완료 — 판정 보류", "complete": False,
                    "notes": ["비교 대상 또는 품질·필수 과제 실행이 부족하다. 표시된 수치는 부분 실행 결과이며 도구 선택 판정은 보류한다."]}

    out = {"arms": S, "decision": decision, "violations": violations, "n_runs": len(metas), "total_cost_usd": round(sum(m["cost_usd"] for m in metas), 3)}
    (RESULTS / "summary-v2.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=list))
    (RESULTS / "report-v2.md").write_text(report(out, metas, arms))
    print((RESULTS / "report-v2.md").read_text())


def fmt(x, d=0):
    return "-" if x is None else f"{x:,.{d}f}"


def report(o, metas, arms):
    S = o["arms"]
    L = ["# Q6 v2(어려운 과제) 결과", "", f"실행 {o['n_runs']}건, API 환산 ${o['total_cost_usd']}", "",
         "## 판정", "", f"**{o['decision']['verdict']}**", ""] + [f"- {n}" for n in o["decision"]["notes"]] + [""]
    L += ["## 점수표", "", "| 도구 | 필수(F1v2·F2) | 거짓 성공 | 품질 | 토큰 효율 | 속도 | 안정성 | 종합 | 흔들림 폭 |", "|---|---|---|---|---|---|---|---|---|"]
    for a in arms:
        s, sc = S[a], S[a]["score"]
        gate_status = '미완료' if s['f1_n'] < 3 or s['f2_n'] < 2 else ('통과' if s['gate_pass'] else '탈락')
        gate = f"{gate_status} ({s['f1_pass']}/{s['f1_n']}·{s['f2_pass']}/{s['f2_n']})"
        L.append(f"| {s['label']} | {gate} | {s['false_success']} | {sc['quality']} | {sc['tokens']} | {sc['speed']} | {sc['stability']} | {sc['composite']} | ±{s['noise_band_points']} |")
    L += ["", "## 품질(성공률과 95% 구간)", "", "| 도구 | 성공 | 95% 구간 | " + " | ".join(QUALITY_KINDS) + " |", "|---|---|---|" + "---|" * len(QUALITY_KINDS)]
    for a in arms:
        s = S[a]
        cells = [f"{s['by_kind'][k]['success']}/{s['by_kind'][k]['n']}" if k in s["by_kind"] else "-" for k in QUALITY_KINDS]
        L.append(f"| {s['label']} | {s['successes']}/{s['n_quality_runs']} | {s['ci95'][0]:.0%}~{s['ci95'][1]:.0%} | " + " | ".join(cells) + " |")
    L += ["", "## 토큰과 시간", "", "| 도구 | 성공 1건당 토큰 | 중앙값 토큰 | 최대 컨텍스트(중앙값/최대) | 도구 시간 중앙값(s) | 전체 시간 중앙값(s) | 성공 1건당 전체 시간(s, 참고) |", "|---|---|---|---|---|---|---|"]
    for a in arms:
        s = S[a]
        L.append(f"| {s['label']} | {fmt(s['tokens_per_success'])} | {fmt(s['median_tokens'])} | {fmt(s['max_context_median'])}/{fmt(s['max_context_max'])} | {fmt(s['median_tool_s'], 1)} | {fmt(s['median_wall_s'], 1)} | {fmt(s['wall_per_success'], 1)} |")
    L += ["", "### 과제별 중앙값 토큰 / 최대 컨텍스트", "", "| 도구 | " + " | ".join(QUALITY_KINDS) + " |", "|---|" + "---|" * len(QUALITY_KINDS)]
    for a in arms:
        s = S[a]
        L.append(f"| {s['label']} | " + " | ".join(f"{fmt(s['by_kind'][k]['median_tokens'])} / {fmt(s['by_kind'][k]['median_max_context'])}" if k in s["by_kind"] else "-" for k in QUALITY_KINDS) + " |")
    L += ["", "## 비밀 관리(F1v2)와 안정성", "", "| 도구 | 코드 정답 | 2회차 비밀번호 노출 | 1회차 입력값 노출 | 도구 오류 | 재시도 | 브라우저 남은 실행 | 상태 파일 |", "|---|---|---|---|---|---|---|---|"]
    for a in arms:
        s = S[a]
        sf = "; ".join(f"{f['path']} {f['mode']}" for f in s["state_files"]) or "-"
        L.append(f"| {s['label']} | {s['f1_code_ok']}/{s['f1_n']} | {s['f1_exposed_runs']}/{s['f1_n']} | {s['f1_echo_run1']}/{s['f1_n']} | {s['tool_errors']} | {s['retries']} | {s['leftover_runs']} | {sf} |")
    L += ["", "## 실행별 결과", "", "| 실행 | 성공 | 실패 유형 | 토큰 | 최대 컨텍스트 | 도구 시간(s) | 비용 | 표시 |", "|---|---|---|---|---|---|---|---|"]
    for m in sorted(metas, key=lambda m: (m["item"]["kind"], m["item"]["task"], m["item"]["arm"], m["item"]["rep"])):
        flags = ",".join(sorted({f["tag"] for f in m["flags"]}))
        mc = max(x["tokens"]["max_context"] for x in m["metrics"])
        L.append(f"| {m['item']['id']} | {'O' if m['judge']['success'] else 'X'} | {m['fail_type'] or ''} | {fmt(m['tokens_total'])} | {fmt(mc)} | {tool_time(m):.1f} | {m['cost_usd']} | {flags} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
