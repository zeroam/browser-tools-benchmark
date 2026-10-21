# Browser tools benchmark

**AI 에이전트가 개발 중 화면을 확인하고, 동작을 검증하고, E2E 테스트를 작성할 때 어떤 브라우저 도구가 잘 맞는지** 비교합니다. 같은 모델과 과제에 도구만 바꿔 끼우며, 로그인 유지·동시 작업·시간·토큰·비용·오류도 봅니다. 모든 웹 대상과 계정은 로컬 더미 데이터입니다.

이 GitHub 레포가 결과·실험 절차·재현 방법의 주 문서입니다.

- [상세 결과와 해석](docs/RESULTS.md): 항목별 점수, 시간·비용·토큰, 선택 근거와 한계.
- [비교 절차와 전체 테스트 목록](docs/METHODOLOGY.md): 무엇을 고정하고 어떤 과제를 어떻게 판정하는가.
- [CLI → E2E 시연](DEMO.md): 개발 세션에서 따라 하는 10~15분 흐름.

## 벤치마크 결과

2026-10-16~17 원본 실험의 **v2 어려운 과제** 결과입니다. 공유본 전체 재실행 점수와 구분합니다.

| 도구 | 품질 | 토큰 효율 | 속도 | 안정성 | 종합 | 필수 조건 | 흔들림 폭 |
|---|---|---|---|---|---|---|---|
| **Playwright CLI** | 100 (42/42) | 99.4 | 66.8 | 95.6 | **94.4** | 통과 (로그인 3/3·동시성 2/2) | ±7.8 |
| agent-browser | 92.9 (39/42) | 88.6 | 61.7 | 86.7 | 86.5 | 통과 (3/3·2/2) | ±14.8 |
| ego lite (창 모드) | 100 (42/42) | 100 | 35.2 | 71.1 | 87.4 | 로그인 복원 탈락 (1/3·2/2) | ±10.3 |
| Playwright MCP | 100 (42/42) | 90.8 | 100 | 73.3 | **95.0** | 로그인 복원 탈락 (2/3·2/2) | ±10.1 |

**종합 = 품질 50% + 토큰 효율 25% + 속도 15% + 안정성 10%.** 효율·속도는 비교 대상 중 가장 좋은 값을 기준으로 환산합니다. 토큰 효율은 성공 1건당 토큰 합계이며 실제 금전 비용과 다릅니다. 흔들림 폭은 반복 실행의 편차를 반영한 값으로, 종합 점수의 95% 신뢰구간은 아닙니다.

결론은 **Playwright CLI 유지**입니다. MCP의 종합은 더 높지만 로그인 복원 필수 조건을 통과하지 못했습니다. CLI와 agent-browser의 점수 차이는 측정 편차 안이라 확실한 우월성을 입증한 결과로 해석하지 않습니다. 사전에 정한 전환 조건을 넘는 대안이 없었습니다.

단일 모델·localhost·과제당 소수 반복의 결과입니다. 모든 모델과 웹사이트에서의 순위로 일반화할 수 없습니다. [v1·v2 상세 점수와 비용, 한계](docs/RESULTS.md)를 참고하세요.

## 어떤 절차로 비교하는가

1. **조건 고정:** 같은 모델·과제·프롬프트 틀·시간/예산 제한을 사용하고 도구·브라우저 버전을 기록합니다. 도구별 사용 안내와 인터페이스만 달라집니다.
2. **독립 실행:** 실행마다 새 작업 폴더·새 브라우저로 시작합니다. 도구 실행 순서를 과제별로 섞습니다. 로그인 복원은 1차 저장 후 별도 브라우저에서, 동시성은 3개 계정으로 확인합니다.
3. **과제 수행:** 에이전트가 브라우저로 조작하고 최종 답 또는 Playwright 테스트 파일을 제출합니다.
4. **외부 판정:** 정답·서버 완료 기록·실제 앱 상태·생성된 테스트의 정상/버그 실행으로 성공을 판정합니다. 에이전트의 성공 보고와 대조해 거짓 성공도 기록합니다.
5. **측정·집계:** 성공률·토큰·비용·시간·오류·남은 브라우저를 모읍니다. 로그인·동시성 필수 조건을 먼저 보고, 점수와 전환 조건으로 판단합니다. 부분 실행은 판정 보류로 표시합니다.

## 어떤 테스트를 하는가

**WebGames 전체를 돌리지 않습니다.** 기본 조작 10개와 어려운 조작 10개를 고르고, 개발·검증 흐름을 재현하는 자체 과제를 추가했습니다.

| 묶음 | 테스트 내용 | 반복과 판정 |
|---|---|---|
| WebGames v1 | 클릭, 날짜, 파일 업로드·다운로드, 키 조합, hover, 드래그, iframe, 여러 탭, 우클릭 | 기본 각 1회, 대표 3개는 총 3회; 일부 창 모드 비교 |
| WebGames v2 | 자동 포커스 입력, 정확한 텍스트, 가로 스크롤, 겹친 팝업, 누른 채 유지, 좌표 클릭, 슬라이더, 인쇄/PDF, 지도 드래그, 우클릭 | 각 3회; 정답과 서버 완료 기록 확인(OTP 예외 있음) |
| F1 / F1v2 | 저장한 로그인 상태를 새 브라우저에서 복원 | v1 2회·v2 3회; v2는 2차 실행의 비밀번호 노출도 검사 |
| F2 | 같은 사이트에 서로 다른 계정 3개로 동시 접속 | 2회; 계정이 섞이지 않아야 함 |
| F3 | 더미 봇 대시보드에서 심어둔 표의 불일치 찾기 | 2회; 정확한 차이 보고·스크린샷 필요 |
| F4 / F4v2 | 탐색 후 Playwright 테스트 작성 | v1 2회·v2 3회; 정상 통과·버그 검출, v2는 버그 6종과 지연 정상도 검사 |
| H1 / H2 / H3 | 400행 표 대조 / 여러 봇·탭에서 20개 값 수집 / 변하는 화면 조작 | 각각 3회; 누락·허위 보고와 잘못된 조작을 판정 |

v2 품질 점수의 분모 **42건 = WebGames 10종 × 3회 + H1·H2·H3·F4v2 4종 × 3회**입니다. 로그인 복원과 동시성은 이 42건 밖의 필수 조건입니다. [개별 과제명·성공 조건·실행 횟수](docs/METHODOLOGY.md)에 전체 목록이 있습니다.

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
