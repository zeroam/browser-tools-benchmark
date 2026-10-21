#!/usr/bin/env python3
"""Aggregate Q6 runs into the score table and apply the pre-registered decision rules.

Weights and rules were fixed on 2026-10-16 before any scored run (Work Brief Q6):
  gates (F1, F2 pass 2/2; false-success count) are shown apart from the composite;
  quality 50 / token efficiency 25 / speed 15 / stability 10.
Writes results/summary.json and results/report.md.
"""
import json
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "runs"
RESULTS = ROOT / "results"
ARM_ORDER = ["pwcli", "agentbrowser", "ego", "pwmcp"]
LABEL = {"pwcli": "Playwright CLI", "agentbrowser": "agent-browser", "ego": "ego lite", "pwmcp": "Playwright MCP"}
MAIN_MODE = {"pwcli": "headless", "agentbrowser": "headless", "ego": "headed", "pwmcp": "headless"}
CANDIDATES = ["agentbrowser", "ego"]  # MCP is the current baseline being removed; scored for reference only
W = {"quality": 0.50, "tokens": 0.25, "speed": 0.15, "stability": 0.10}


def load():
    from score_v2 import fix_ego_leftover
    metas = []
    for p in sorted(RUNS.glob("*/meta.json")):
        # v1 only: v2 (`v2-`) and the ego same-window controls (`v2c-`) have their own reports
        if p.parent.name.startswith(("pilot-", "v2-", "v2c-")):
            continue
        m = json.loads(p.read_text())
        if m["item"]["arm"] == "ego":
            fix_ego_leftover(m)
        metas.append(m)
    return metas


def med(xs):
    return st.median(xs) if xs else None


def rel_spread(xs):
    m = med(xs)
    return (max(xs) - min(xs)) / m if xs and m else 0.0


def main():
    metas = load()
    by = {}
    for m in metas:
        it = m["item"]
        by.setdefault(it["arm"], []).append(m)
    arms = [a for a in ARM_ORDER if a in by]
    S = {}
    for a in arms:
        runs = by[a]
        main_runs = [m for m in runs if m["item"]["mode"] == MAIN_MODE[a]]
        q_runs = [m for m in main_runs if (m["item"]["kind"] == "wg" and m["item"]["rep"] == 0)
                  or m["item"]["kind"] in ("f3", "f4")]
        f1 = [m for m in main_runs if m["item"]["kind"] == "f1"]
        f2 = [m for m in main_runs if m["item"]["kind"] == "f2"]
        succ = sum(1 for m in q_runs if m["judge"]["success"])
        tok_sum = sum(m["tokens_total"] for m in q_runs)
        var_runs = [m for m in main_runs if m["item"]["kind"] == "wg"]
        var_tasks = {}
        for m in var_runs:
            var_tasks.setdefault(m["item"]["task"], []).append(m)
        var_tasks = {t: v for t, v in var_tasks.items() if len(v) >= 3}
        S[a] = {
            "label": LABEL[a],
            "mode": MAIN_MODE[a],
            "n_quality_runs": len(q_runs),
            "f1_pass": sum(1 for m in f1 if m["judge"]["success"]), "f1_n": len(f1),
            "f2_pass": sum(1 for m in f2 if m["judge"]["success"]), "f2_n": len(f2),
            "false_success": sum(1 for m in main_runs if m["judge"].get("false_success")),
            "successes": succ,
            "tokens_per_success": (tok_sum / succ) if succ else None,
            "median_tokens": med([m["tokens_total"] for m in q_runs]),
            "median_wall_s": med([m["wall_s"] for m in q_runs]),
            "stable_share": (sum(1 for m in main_runs if m["stable"]) / len(main_runs)) if main_runs else 0,
            "cost_usd": round(sum(m["cost_usd"] for m in runs), 3),
            "fixed_overhead_median": med([m["metrics"][0]["tokens"]["fixed_overhead"] for m in q_runs]),
            "max_context_max": max([x["tokens"]["max_context"] for m in q_runs for x in m["metrics"]] or [0]),
            "tool_output_tokens_median": med([sum(x["tokens"]["tool_output_est_tokens"] for x in m["metrics"]) for m in q_runs]),
            "tool_calls_median": med([sum(x["tool_calls"] for x in m["metrics"]) for m in q_runs]),
            "turns_median": med([sum(x["num_turns"] or 0 for x in m["metrics"]) for m in q_runs]),
            "tool_errors": sum(x["tool_errors"] for m in main_runs for x in m["metrics"]),
            "retries": sum(x["retries"] for m in main_runs for x in m["metrics"]),
            "leftover_runs": sum(1 for m in main_runs if any(e["leftover_browser_procs"] for e in m["exec"])
                                 or (a == "ego" and any((f.get("leftover_sessions") or 0) > 0 for f in m["finish"]))),
            "peak_browser_mb_median": med([max(e["max_browser_mb"] for e in m["exec"]) for m in q_runs]),
            "peak_browser_mb_max": max([e["max_browser_mb"] for m in main_runs for e in m["exec"]] or [0]),
            "flags": sum(len(m["flags"]) for m in runs),
            "fail_types": {},
            "state_files": [f for m in f1 for f in m["judge"].get("state_files", [])],
            "variance": {
                t: {"success": [m["judge"]["success"] for m in v], "tokens": [m["tokens_total"] for m in v],
                    "wall_s": [m["wall_s"] for m in v]} for t, v in var_tasks.items()},
        }
        for m in q_runs:
            if m["fail_type"]:
                S[a]["fail_types"][m["fail_type"]] = S[a]["fail_types"].get(m["fail_type"], 0) + 1
        v = S[a]["variance"]
        S[a]["noise"] = {
            "token_rel": med([rel_spread(x["tokens"]) for x in v.values()]) or 0.0,
            "time_rel": med([rel_spread(x["wall_s"]) for x in v.values()]) or 0.0,
            "flip_tasks": sum(1 for x in v.values() if len(set(x["success"])) > 1),
        }
        S[a]["gate_pass"] = (S[a]["f1_n"] >= 2 and S[a]["f1_pass"] == S[a]["f1_n"]
                             and S[a]["f2_n"] >= 2 and S[a]["f2_pass"] == S[a]["f2_n"])

    # category scores
    tps = [S[a]["tokens_per_success"] for a in arms if S[a]["tokens_per_success"]]
    spd = [S[a]["median_wall_s"] for a in arms if S[a]["median_wall_s"]]
    for a in arms:
        s = S[a]
        n = s["n_quality_runs"] or 14
        s["score"] = {
            "quality": round(100 * s["successes"] / n, 1),
            "tokens": round(100 * min(tps) / s["tokens_per_success"], 1) if s["tokens_per_success"] else 0.0,
            "speed": round(100 * min(spd) / s["median_wall_s"], 1) if s["median_wall_s"] else 0.0,
            "stability": round(100 * s["stable_share"], 1),
        }
        s["score"]["composite"] = round(sum(W[k] * s["score"][k] for k in W), 1)
        nz = s["noise"]
        s["noise_band_points"] = round(50 * nz["flip_tasks"] / n + 25 * nz["token_rel"] + 15 * nz["time_rel"], 1)

    # decision rules
    decision = {"keep": "pwcli", "notes": []}
    pw = S.get("pwcli")
    if pw and not pw["gate_pass"]:
        decision["notes"].append("Playwright CLI가 필수 조건(F1·F2)을 통과하지 못했다. 원인을 확인한 뒤 다시 판정한다(규칙 5).")
    for a in CANDIDATES:
        if a not in S or not pw:
            continue
        s = S[a]
        why = []
        if not s["gate_pass"]:
            decision["notes"].append(f"{s['label']}: 필수 조건 탈락(F1 {s['f1_pass']}/{s['f1_n']}, F2 {s['f2_pass']}/{s['f2_n']}).")
            continue
        if s["false_success"] > pw["false_success"]:
            decision["notes"].append(f"{s['label']}: 거짓 성공 {s['false_success']}건 > Playwright CLI {pw['false_success']}건이라 전환 후보에서 제외(규칙 3).")
            continue
        flip_band = max(s["noise"]["flip_tasks"], pw["noise"]["flip_tasks"])
        diff = s["successes"] - pw["successes"]
        if diff >= 3 and diff > flip_band:
            why.append(f"성공 {diff}개 더 많음")
        if s["successes"] >= pw["successes"]:
            tok_gain = 1 - s["median_tokens"] / pw["median_tokens"] if pw["median_tokens"] else 0
            time_gain = 1 - s["median_wall_s"] / pw["median_wall_s"] if pw["median_wall_s"] else 0
            tok_band = max(s["noise"]["token_rel"], pw["noise"]["token_rel"])
            time_band = max(s["noise"]["time_rel"], pw["noise"]["time_rel"])
            if tok_gain >= 0.40 and tok_gain > tok_band:
                why.append(f"중앙값 토큰 {tok_gain:.0%} 적음")
            if time_gain >= 0.40 and time_gain > time_band:
                why.append(f"중앙값 시간 {time_gain:.0%} 짧음")
        if why:
            decision["notes"].append(f"{s['label']}: 전환 조건 충족({', '.join(why)}). 전환을 제안한다.")
            decision.setdefault("switch_candidates", []).append(a)
        else:
            decision["notes"].append(f"{s['label']}: 필수 조건은 통과했지만 전환 조건(성공 +3 또는 토큰·시간 40%↓)을 넘지 못했다.")
    for a in arms:
        if S[a]["leftover_runs"]:
            decision["notes"].append(f"{S[a]['label']}: 실행 뒤 브라우저가 남은 실행 {S[a]['leftover_runs']}건. 무인 운용 전 정리 방법을 정한다(규칙 6).")
    if not decision.get("switch_candidates"):
        decision["verdict"] = "Playwright CLI 유지"
    else:
        decision["verdict"] = "전환 제안: " + ", ".join(LABEL[a] for a in decision["switch_candidates"])

    # window mode comparison (paired WebGames tasks)
    window = {}
    for a in ("pwcli", "agentbrowser"):
        if a not in by:
            continue
        hl = {m["item"]["task"]: m for m in by[a] if m["item"]["kind"] == "wg" and m["item"]["rep"] == 0 and m["item"]["mode"] == "headless"}
        hd = {m["item"]["task"]: m for m in by[a] if m["item"]["kind"] == "wg" and m["item"]["rep"] == 0 and m["item"]["mode"] == "headed"}
        pairs = sorted(set(hl) & set(hd))
        if not pairs:
            continue
        sh = sum(hl[t]["judge"]["success"] for t in pairs)
        sd = sum(hd[t]["judge"]["success"] for t in pairs)
        th, td = med([hl[t]["tokens_total"] for t in pairs]), med([hd[t]["tokens_total"] for t in pairs])
        wh, wd = med([hl[t]["wall_s"] for t in pairs]), med([hd[t]["wall_s"] for t in pairs])
        tok_save = 1 - th / td if td else 0
        time_save = 1 - wh / wd if wd else 0
        concl = ("창 없는 모드를 무인 운용·E2E 기본으로 확정" if sh >= sd and (tok_save >= 0.20 or time_save >= 0.20)
                 else "관찰이 필요할 때는 창을 띄워도 손해가 없다")
        window[a] = {"pairs": len(pairs), "success_headless": sh, "success_headed": sd, "median_tokens_headless": th,
                     "median_tokens_headed": td, "median_wall_headless": wh, "median_wall_headed": wd,
                     "token_saving": round(tok_save, 3), "time_saving": round(time_save, 3), "conclusion": concl}

    ranked = sorted([a for a in arms if S[a]["gate_pass"]], key=lambda a: -S[a]["score"]["composite"])
    complete = (len(arms) >= 2 and "pwcli" in S and all(
        S[a]["n_quality_runs"] >= 14 and S[a]["f1_n"] >= 2 and S[a]["f2_n"] >= 2
        for a in arms))
    if not complete:
        decision = {"verdict": "실험 미완료 — 판정 보류", "complete": False,
                    "notes": ["비교 대상 또는 품질·필수 과제 실행이 부족하다. 표시된 수치는 부분 실행 결과이며 도구 선택 판정은 보류한다."]}
        ranked = []

    out = {"arms": S, "decision": decision, "window": window, "ranking": ranked,
           "total_cost_usd": round(sum(m["cost_usd"] for m in metas), 3), "n_runs": len(metas)}
    (RESULTS / "summary.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
    (RESULTS / "report.md").write_text(report(out, metas))
    print((RESULTS / "report.md").read_text())


def fmt(x, d=0):
    if x is None:
        return "-"
    return f"{x:,.{d}f}"


def report(o, metas):
    S, arms = o["arms"], [a for a in ARM_ORDER if a in o["arms"]]
    L = ["# Q6 브라우저 도구 실측 결과", "", f"실행 {o['n_runs']}건, API 환산 ${o['total_cost_usd']}", ""]
    L += ["## 판정", "", f"**{o['decision']['verdict']}**", ""] + [f"- {n}" for n in o["decision"]["notes"]] + [""]
    L += ["## 점수표", "", "| 도구 | 필수(F1·F2) | 거짓 성공 | 품질 | 토큰 효율 | 속도 | 안정성 | 종합 | 흔들림 폭 |", "|---|---|---|---|---|---|---|---|---|"]
    for a in arms:
        s = S[a]
        gate_status = '미완료' if s['f1_n'] < 2 or s['f2_n'] < 2 else ('통과' if s['gate_pass'] else '탈락')
        gate = f"{gate_status} ({s['f1_pass']}/{s['f1_n']}·{s['f2_pass']}/{s['f2_n']})"
        sc = s["score"]
        L.append(f"| {s['label']} ({s['mode']}) | {gate} | {s['false_success']} | {sc['quality']} | {sc['tokens']} | {sc['speed']} | {sc['stability']} | {sc['composite']} | ±{s['noise_band_points']} |")
    L += ["", "종합 = 품질×0.5 + 토큰 효율×0.25 + 속도×0.15 + 안정성×0.1. 필수 조건 탈락 도구는 순위에서 뺀다. "
          "종합 차이가 흔들림 폭보다 작으면 동점이다.", ""]
    L += ["## 품질과 토큰", "", "| 도구 | 성공/14 | 성공 1건당 토큰 | 중앙값 토큰 | 고정 부담 | 최대 컨텍스트 | 도구 출력(추정 토큰) | 도구 호출 | 중앙값 시간(s) | 실패 유형 |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for a in arms:
        s = S[a]
        ft = ", ".join(f"{k} {v}" for k, v in s["fail_types"].items()) or "-"
        L.append(f"| {s['label']} | {s['successes']}/{s['n_quality_runs']} | {fmt(s['tokens_per_success'])} | {fmt(s['median_tokens'])} | {fmt(s['fixed_overhead_median'])} | {fmt(s['max_context_max'])} | {fmt(s['tool_output_tokens_median'])} | {fmt(s['tool_calls_median'])} | {fmt(s['median_wall_s'], 1)} | {ft} |")
    L += ["", "## 운영 안정성과 상태 파일", "", "| 도구 | 도구 오류 | 재시도 | 브라우저 남은 실행 | 최대 메모리 중앙값(MB) | 최대 메모리(MB) | F1 상태 파일 |", "|---|---|---|---|---|---|---|"]
    for a in arms:
        s = S[a]
        sf = "; ".join(f"{f['path']} {f['mode']} 평문PW={'예' if f['plaintext_password'] else '아니오'}" for f in s["state_files"])
        if not sf:
            sf = "작업 폴더에 상태 파일 없음(도구 자체 저장소 사용)" if s["f1_n"] else "-"
        L.append(f"| {s['label']} | {s['tool_errors']} | {s['retries']} | {s['leftover_runs']} | {fmt(s['peak_browser_mb_median'])} | {fmt(s['peak_browser_mb_max'])} | {sf} |")
    L += ["", "## 편차(같은 조건 3회)", "", "| 도구 | 과제 | 성공 | 토큰 | 시간(s) |", "|---|---|---|---|---|"]
    for a in arms:
        for t, v in S[a]["variance"].items():
            L.append(f"| {S[a]['label']} | {t} | {''.join('O' if x else 'X' for x in v['success'])} | {', '.join(fmt(x) for x in v['tokens'])} | {', '.join(fmt(x, 1) for x in v['wall_s'])} |")
    if o["window"]:
        L += ["", "## 창 모드 비교(WebGames 같은 과제끼리)", "", "| 도구 | 성공(창 없음/창) | 중앙값 토큰(창 없음/창) | 중앙값 시간(창 없음/창) | 결론 |", "|---|---|---|---|---|"]
        for a, w in o["window"].items():
            L.append(f"| {LABEL[a]} | {w['success_headless']}/{w['success_headed']} of {w['pairs']} | {fmt(w['median_tokens_headless'])}/{fmt(w['median_tokens_headed'])} ({w['token_saving']:+.0%}) | {fmt(w['median_wall_headless'], 1)}/{fmt(w['median_wall_headed'], 1)} ({w['time_saving']:+.0%}) | {w['conclusion']} |")
    L += ["", "## 실행별 결과", "", "| 실행 | 성공 | 실패 유형 | 토큰 | 시간(s) | 비용 | 표시 |", "|---|---|---|---|---|---|---|"]
    for m in sorted(metas, key=lambda m: (m["item"]["kind"], m["item"]["task"], m["item"]["arm"], m["item"]["mode"], m["item"]["rep"])):
        flags = ",".join(sorted({f["tag"] for f in m["flags"]})) or ""
        L.append(f"| {m['item']['id']} | {'O' if m['judge']['success'] else 'X'} | {m['fail_type'] or ''} | {fmt(m['tokens_total'])} | {m['wall_s']} | {m['cost_usd']} | {flags} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
