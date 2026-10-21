# Browser tools benchmark

같은 모델과 과제에 브라우저 도구만 바꿔 끼우는 실험입니다. Playwright CLI로 화면을 탐색하고 E2E 테스트로 옮기는 짧은 시연도 포함합니다. 모든 웹 대상과 계정은 로컬 더미 데이터입니다.

## 먼저 5분 만에 실행하기

Python 3.10+, Node 22+, npm, Google Chrome이 필요합니다. 데모·E2E에는 AI 계정이나 모델 호출 비용이 없습니다. macOS에서 검증했으며 Linux는 미검증입니다.

```sh
npm ci --prefix tools
python3 demo.py verify
```

예상 결과는 `normal`, `slow` 통과와 `bug-*` 6종 검출입니다. 버그 앱의 테스트 실패는 **예상한 assertion 실패인지** 확인합니다. 브라우저 미설치·서버 오류는 검출 성공으로 세지 않습니다. 상세 결과는 `.demo/summary.json`에 생깁니다.

Chrome 대신 bundled Chromium을 쓰려면:

```sh
cd tools
npx playwright install chromium
cd ..
PW_CHANNEL=chromium python3 demo.py verify
```

## 개발 세션 시연

[DEMO.md](DEMO.md)의 10~15분 순서를 사용합니다.

1. CLI로 봇 목록 → 상세 → 포지션 표를 탐색합니다.
2. 출력되는 Playwright 코드와 locator를 E2E 테스트로 옮깁니다.
3. 정상 앱 통과를 확인하고, 표의 값·행·이동을 바꾼 앱에서 같은 테스트가 실패하는지 봅니다.
4. 시간 여유가 있으면 같은 과제를 다른 브라우저 도구로 실행해 비용·토큰·판정을 비교합니다.

## 원본 도구 비교 실험 재실행

`bench.py`는 2026-10-16~17 실험의 과제·프롬프트·판정기·스케줄을 가져온 실행기입니다. 비교 실행에는 별도로 로그인된 Claude Code가 필요합니다. AI는 로컬 파일 작성과 셸 실행 권한을 사용하므로 **개인 설정과 작업물이 없는 전용 OS 사용자/실험 맥**을 권장합니다. 실행 cwd를 분리하는 것은 보안 sandbox가 아닙니다.

원본 도구 버전:

| 도구 | 버전 |
|---|---|
| Playwright CLI | 0.1.22 |
| agent-browser | 0.27.0 |
| Playwright MCP | 0.0.83 |
| Playwright Test | 1.64.1 |
| ego lite (선택) | 0.6.0.12 |
| Claude Code | 2.1.301 |
| 모델 | claude-sonnet-5-5 |
| Google Chrome | 155 |

`tools/package-lock.json`으로 MCP와 Test의 실제 설치 버전을 고정했습니다. CLI·agent-browser와 Claude Code는 별도 설치합니다. 다른 버전·모델을 사용하면 변경한 조건을 결과와 함께 공유하세요. 동일 과제와 판정의 재현이며 과거 점수의 일치를 보장하지 않습니다.

```sh
# 전용 실험 환경에서 실행
npm install -g @playwright/cli@0.1.22 agent-browser@0.27.0
npm ci --prefix tools
sh bin/build-webgames.sh
python3 bench.py versions
python3 bench.py schedule
python3 bench.py schedule-v2
python3 bench.py serve
```

서버는 foreground로 유지됩니다. 다른 터미널에서 우선 1건만 실행합니다:

```sh
# F3: 심어둔 불일치 찾기. 원본 v1의 1건을 실행한다.
BENCH_BUDGET_USD=2 python3 bench.py one f3-f3-pwcli-headless-r0

# 같은 과제를 세 도구로 비교 (각 도구의 설치·인증 먼저 확인)
BENCH_BUDGET_USD=5 python3 bench.py run --only \
  f3-f3-pwcli-headless-r0 \
  f3-f3-agentbrowser-headless-r0 \
  f3-f3-pwmcp-headless-r0
```

실행별 `runs/<ID>/meta.json`의 `judge`, `cost_usd`, `tokens_total`, `wall_s`를 비교합니다. `stream.jsonl`은 상세 도구 기록이고 더미 비밀번호를 포함할 수 있으므로 기본 공유 대상에서 제외합니다. agent cwd는 레포의 형제 디렉터리 `<레포명>-work/`에 둡니다. 완료된 run은 건너뛰며 `--force`는 해당 ID의 로그·작업물을 교체합니다.

전체 비교(선택, 유료):

```sh
# 기본 예산은 누적 $5. 원본 전체는 API 환산 약 $26.29였지만 재실행 비용은 달라진다.
BENCH_BUDGET_USD=50 python3 bench.py run --arms pwcli,agentbrowser,pwmcp
BENCH_BUDGET_USD=50 python3 bench.py run --schedule schedule-v2.json --arms pwcli,agentbrowser,pwmcp
python3 score.py
python3 score_v2.py
```

예산은 완료 로그 기준의 실행 전 gate이며 서버 과금의 강제 상한이 아닙니다. F1은 두 번, F2는 동시 세 번의 AI 호출을 사용합니다. `BENCH_MODEL`로 모델을 바꿀 수 있습니다. 리포트는 실행한 subset의 점수입니다. 품질·필수 과제 또는 비교 대상이 부족하면 도구 선택은 `판정 보류`로 표시합니다. 필수 조건(F1/F2)을 실행하지 않은 파일로 도구 전환 결론을 내리지 마세요.

ego는 창 모드만 지원하고 앱 단위 작업 공간을 정리합니다. 전용 macOS 계정에서 다른 ego 작업이 없을 때만 `BENCH_EGO_ISOLATED=1`로 켜세요. 공유본은 앱 종료·재시작이나 전역 skill 링크 삭제를 하지 않습니다. ego 설치가 전역 skill을 생성하는 동작은 이 실행기가 막지 않습니다.

`serve` 터미널의 Ctrl-C는 그 실행이 띄운 서버만 종료합니다. CLI·agent-browser 정리도 작업별 지정 세션만 닫습니다. AI가 직접 만든 별도 이름의 세션은 전역 종료하지 않으므로 전용 계정에서 잔여물을 확인하세요.

## 과제와 판정

- v1: WebGames 조작 10개, 로그인 상태 파일 복원(F1), 동시 계정 분리(F2), 불일치 찾기(F3), E2E 작성(F4).
- v2: 어려운 WebGames 10개, 큰 표(H1), 긴 흐름(H2), 변하는 화면(H3), 6종 버그 검출·늦게 뜨는 정상 앱(F4v2), 비밀번호 노출 없이 로그인 복원(F1v2).
- WebGames v2는 정답과 서버 완료 기록을 함께 확인합니다(otp-entry 예외는 소스에 명시).
- 성공 보고만 믿지 않고 앱 상태와 생성된 테스트의 정상/버그 실행을 판정합니다.
- 점수: 품질 50%, 토큰 효율 25%, 속도 15%, 안정성 10%. 로그인 복원과 동시성은 별도 필수 조건입니다.

## 원본 결과와 공유본의 차이

원본 v2 품질 과제 42건에서 CLI 42/42, agent-browser 39/42, MCP 42/42, ego 42/42였습니다. MCP와 ego는 별도 로그인 복원 필수 조건에서 탈락했습니다. 결론은 CLI 유지였고, 단일 모델·localhost·과제당 3회라는 한계가 있습니다. 품질 42건과 필수 과제는 별도 분모입니다.

공유본은 원본의 개인 경로·Node 경로를 없애고, CLI와 agent-browser에 작업별 세션을 지정합니다. 전역 종료와 전역 skill 삭제를 제거하고, 서버를 Ctrl-C로 정리하게 바꿨습니다. 원본의 `~/Downloads` 이동도 제거했습니다. 따라서 운영 안정성·잔여 프로세스 수치는 역사적 결과와 직접 같다고 볼 수 없습니다. 원본 341건을 이 공유본으로 다시 실행한 것은 아닙니다.

도구 안내문은 재실행 시 설치된 공식 skill에서 생성합니다. 원본 실행의 안내문·원시 로그·사용자 설정은 포함하지 않습니다. WebGames는 당시 작업 디렉터리의 소스 snapshot입니다. 기록된 upstream 기준은 `309866f`(2025-06-02)이나 `.git` 없는 snapshot이라 upstream과의 무수정 일치는 검증하지 않았습니다.

## 공유본 검증 (2026-10-21)

- macOS, Node 22.22.3, Chrome 155, Playwright Test 1.64.1.
- 정상·지연 정상 통과, 버그 6종 모두 검출.
- WebGames dependency 설치 및 production build 통과.
- 원본 F3 CLI 과제 성공: 불일치 1건 정확히 탐지, 스크린샷 있음, 거짓 성공 0, 17.1초, API 환산 $0.0493. Claude Code는 2.1.305로 원본과 다릅니다.
- 부분 실행 판정 보류 회귀 검증: `python3 -m unittest discover -s tests -v`.
- 전체 341건 재실행, Linux, ego 실행은 이 공유본에서 미검증입니다.

## 출처와 라이선스

- [WebGames](https://github.com/convergence-ai/webgames): Apache-2.0, `webgames/LICENSE` 보존. 이 레포는 당시 사용한 소스 snapshot을 포함합니다.
- [Playwright CLI](https://github.com/microsoft/playwright-cli): 명령 문법과 공식 skill.
- [Playwright assertions](https://playwright.dev/docs/test-assertions): 재시도하는 locator assertion.
- [agent-browser](https://github.com/vercel-labs/agent-browser), [Playwright MCP](https://github.com/microsoft/playwright-mcp), [ego lite](https://github.com/citrolabs/ego-lite).

레포 코드는 Apache-2.0입니다. 외부 도구의 바이너리는 포함하지 않으며 각 배포처의 라이선스와 설치 절차를 따릅니다.
