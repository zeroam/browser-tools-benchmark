#!/usr/bin/env python3
"""Same-window control for ego (reference only, not part of the pre-registered verdict).

ego has no headless mode and ran a day after the other arms, so the v2 verdict compares ego (headed, 2026-10-17)
with the other arms (headless, 2026-10-16). To see how much of the gap is mode/time rather than the tool, the ego
schedule interleaved a Playwright CLI headed run (`v2c-*`) with every ego v2 run, task by task.
Writes results/report-ego-control.md.
"""
import json
import statistics as st

import score_v2 as s2

GROUPS = [
    ("ego lite · 창 모드 · 10/17", lambda m: m["item"]["id"].startswith("v2-") and m["item"]["arm"] == "ego"),
    ("Playwright CLI · 창 모드 · 10/17 (대조)", lambda m: m["item"]["id"].startswith("v2c-")),
    ("Playwright CLI · 창 없음 · 10/16 (v2 본 실행)", lambda m: m["item"]["id"].startswith("v2-") and m["item"]["arm"] == "pwcli"),
]


def load_all():
    metas = s2.load()
    for p in sorted(s2.RUNS.glob("v2c-*/meta.json")):
        m = json.loads(p.read_text())
        for i, x in enumerate(m["metrics"]):
            if "duration_api_ms" not in x:
                d = p.parent
                streams = {"f1v2": [d / "r1/stream.jsonl", d / "r2/stream.jsonl"]}.get(m["item"]["kind"], [d / "stream.jsonl"])
                last = json.loads(streams[i].read_text().strip().splitlines()[-1])
                x["duration_api_ms"], x["duration_ms"] = last.get("duration_api_ms"), last.get("duration_ms")
        metas.append(m)
    return metas


def summarize(runs):
    q = [m for m in runs if m["item"]["kind"] in s2.QUALITY_KINDS]
    succ = sum(m["judge"]["success"] for m in q)
    f1 = [m for m in runs if m["item"]["kind"] == "f1v2"]
    return {
        "n": len(q), "succ": succ,
        "f1": f"{sum(m['judge']['success'] for m in f1)}/{len(f1)}",
        "tps": sum(m["tokens_total"] for m in q) / succ if succ else None,
        "med_tok": s2.med([m["tokens_total"] for m in q]),
        "med_tool": s2.med([s2.tool_time(m) for m in q]),
        "med_wall": s2.med([m["wall_s"] for m in q]),
        "wps": sum(m["wall_s"] for m in q) / succ if succ else None,
        "stable": sum(m["stable"] for m in runs) / len(runs) if runs else 0,
        "errors": sum(x["tool_errors"] for m in runs for x in m["metrics"]),
        "by_kind": {k: s2.med([m["tokens_total"] for m in q if m["item"]["kind"] == k]) for k in s2.QUALITY_KINDS},
        "cost": sum(m["cost_usd"] for m in runs),
    }


def main():
    metas = load_all()
    S = [(label, summarize([m for m in metas if pick(m)])) for label, pick in GROUPS]
    f = s2.fmt
    L = ["# ego 같은 시간대 대조(참고, 판정 제외)", "",
         "ego는 창 없는 모드가 없고 하루 늦게 돌았다. 그래서 같은 시간대에 같은 과제를 Playwright CLI 창 모드로 번갈아 돌렸다.", "",
         "| 묶음 | 품질 | F1v2 | 성공 1건당 토큰 | 중앙값 토큰 | 도구 시간 중앙값(s) | 전체 시간 중앙값(s) | 성공 1건당 전체 시간(s) | 안정 실행 비율 | 도구 오류 | 비용($) |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for label, s in S:
        L.append(f"| {label} | {s['succ']}/{s['n']} | {s['f1']} | {f(s['tps'])} | {f(s['med_tok'])} | {f(s['med_tool'], 1)} | "
                 f"{f(s['med_wall'], 1)} | {f(s['wps'], 1)} | {s['stable']:.0%} | {s['errors']} | {s['cost']:.2f} |")
    L += ["", "## 과제별 중앙값 토큰", "", "| 묶음 | " + " | ".join(s2.QUALITY_KINDS) + " |", "|---|" + "---|" * len(s2.QUALITY_KINDS)]
    for label, s in S:
        L.append(f"| {label} | " + " | ".join(f(s["by_kind"][k]) for k in s2.QUALITY_KINDS) + " |")
    ego, ctl = S[0][1], S[1][1]
    L += ["", "## 같은 시간대·같은 창 모드 차이(ego − CLI)", "",
          f"- 성공 1건당 토큰: {ego['tps'] / ctl['tps'] - 1:+.0%}",
          f"- 중앙값 토큰: {ego['med_tok'] / ctl['med_tok'] - 1:+.0%}",
          f"- 도구 시간 중앙값: {ego['med_tool'] / ctl['med_tool'] - 1:+.0%}",
          f"- 성공 1건당 전체 시간: {ego['wps'] / ctl['wps'] - 1:+.0%}"]
    (s2.RESULTS / "report-ego-control.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
