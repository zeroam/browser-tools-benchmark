# 개발 세션 시연 (10~15분)

목표는 화면을 탐색한 뒤 그 흐름을 반복 실행 가능한 테스트로 옮기고, 그 테스트가 실제 오류를 잡는지 확인하는 것입니다. 실제 봇·계정은 사용하지 않습니다.

## v1·v2 전체 과제를 동시에 시연하려면

```sh
python3 bench.py demo --parallel
```

설치와 Claude Code 로그인이 끝난 환경에서 실행합니다. **v1 34항목과 v2 45항목**을 함께 시작하며, 각 과제는 독립 브라우저 세션을 사용합니다. 터미널에서 진행과 결과를 보고, `playwright-cli show` 대시보드에서 새로 나타나는 `bench-…` 세션을 선택해 조작을 관찰합니다. 대시보드는 이 명령과 별도로 열고 닫습니다.

전체 시연은 수십 분 이상 걸릴 수 있고 모델 호출 비용이 듭니다. 기본 누적 예산 gate는 $15이며 `--budget-usd`로 바꿀 수 있습니다. 완료된 항목은 재실행하지 않습니다. `--parallel`을 빼면 v1 → v2 순서입니다. 병렬 실행의 시간은 기존 순차 측정과 구분합니다. 아래는 일부 흐름을 짧게 설명하는 10~15분 시연입니다.

## 시작 전 (발표자가 미리)

README의 설치를 마치고 `python3 demo.py verify`가 8종 모두 PASS인지 확인합니다. Playwright CLI 0.1.22가 필요합니다. 서버 터미널:

```sh
python3 demo.py serve
```

브라우저 주소는 `http://demo.localhost:5420/`입니다. 포트가 사용 중이면 `--port 5421`을 쓰고 이후 CLI URL·`DEMO_URL`·`mode --port`를 모두 맞춥니다. 서버를 끝내면 더미 상태가 초기화됩니다.

## 1. CLI로 화면 탐색 (3분)

별도 터미널에서 고유 세션을 만들고 snapshot을 봅니다.

```sh
DEMO_SESSION="demo-$(date +%s)-$$"
DEMO_OUTPUT="/tmp/playwright-cli/$DEMO_SESSION"
mkdir -p "$DEMO_OUTPUT"
PLAYWRIGHT_MCP_OUTPUT_DIR="$DEMO_OUTPUT" playwright-cli -s="$DEMO_SESSION" open http://demo.localhost:5420/
playwright-cli -s="$DEMO_SESSION" snapshot
```

snapshot의 `alpha-trend` 링크에 붙은 **현재 ref**를 확인한 뒤 다음처럼 누릅니다. `eN`을 실제 값으로 바꿉니다. ref를 예제의 고정 번호로 복사하지 않습니다.

```sh
playwright-cli -s="$DEMO_SESSION" click eN
playwright-cli -s="$DEMO_SESSION" snapshot
playwright-cli -s="$DEMO_SESSION" console error
```

표는 약 0.4초 뒤 나타납니다. 아직 보이지 않으면 snapshot을 다시 봅니다. 화면은 봇 목록과 alpha-trend의 5개 포지션입니다. CLI가 명령과 함께 보여주는 Playwright 코드를 설명합니다.

같은 맥에서 관객과 볼 때 `playwright-cli show`를 열고 세션 이름을 안내합니다. 대시보드에는 그 맥의 다른 세션도 보이므로 전용 시연 환경을 씁니다. 사람이 조작하는 동안 에이전트 조작은 멈춥니다. 원격 관찰은 loopback 포트를 SSH 터널로 연결하고 공인 주소에 대시보드를 열지 않습니다.

## 2. E2E로 옮기기 (4분)

`tools/demo/positions.spec.ts`를 열고 탐색 흐름과 대조합니다.

- `getByRole('link', { name: 'alpha-trend', exact: true })`로 실제 사용자의 클릭을 재현합니다.
- 상세 제목, 정확히 5행, 모든 셀의 기대값을 검증합니다.
- API 응답에서 기대값을 다시 만들지 않습니다. 잘못된 응답을 정답으로 삼을 수 있기 때문입니다.
- 표가 늦게 나타나도 locator assertion이 기다리므로 고정 sleep을 넣지 않습니다.

다음 명령은 정상 앱에서 통과합니다.

```sh
node tools/node_modules/@playwright/test/cli.js test --config tools/playwright.config.ts
```

에이전트에게 탐색·작성을 실제로 보여줄 때의 요청 예:

> Playwright CLI로 http://demo.localhost:5420/의 alpha-trend 상세를 탐색해줘. BTC LONG 0.120 61250.5, ETH SHORT 1.500 2410.2, SOL LONG 30.00 142.35, XRP LONG 2500 0.5821, ADA SHORT 4000 0.3375가 정확히 5행인지 확인하는 테스트를 tools/demo/generated.spec.ts로 작성해줘. 기존 positions.spec.ts는 참고 정답이니 읽지 말고, tools/playwright.config.ts를 사용해 생성한 파일만 실행해줘. 끝나면 자신의 CLI 세션만 닫아줘.

직접 생성한 테스트는 별도 파일명 인자를 주어 실행합니다. `demo.py verify`는 배포된 기준 spec 하나만 실행하므로 생성한 테스트와 섞이지 않습니다.

## 3. 버그를 잡는지 확인 (3분)

```sh
python3 demo.py mode bug-value
node tools/node_modules/@playwright/test/cli.js test --config tools/playwright.config.ts
```

ETH 수량이 9.999로 바뀌어 **같은 테스트가 실패**해야 합니다. 다음은 링크가 다른 봇을 여는 버그입니다.

```sh
python3 demo.py mode bug-nav
node tools/node_modules/@playwright/test/cli.js test --config tools/playwright.config.ts
python3 demo.py mode normal
```

정상/지연 정상/버그 6종을 한 번에 판정하려면 `python3 demo.py verify`를 사용합니다. 별도 임시 포트의 서버를 띄우므로 현재 시연 서버의 mode는 바꾸지 않습니다.

## 4. 비교 실험 (선택 3~5분+)

README의 `bench.py one f3-f3-pwcli-headless-r0`를 실행합니다. 이것은 위의 고정 예제 테스트와 달리 AI가 직접 심어진 불일치를 찾아내는 **원본 과제**입니다. 최종 보고와 `meta.json`의 판정을 대조하고, 토큰·실제 API 환산 비용·시간을 봅니다. 같은 ID의 도구 부분을 바꿔 반복합니다. 모델과 모든 프롬프트를 같게 두고 도구만 바꿔야 비교가 됩니다.

## 끝내기

```sh
playwright-cli -s="$DEMO_SESSION" close
```

직접 띄운 서버 터미널에서 Ctrl-C를 누릅니다. `show`를 켰다면 그 대시보드 창·프로세스도 확인해 닫습니다. `close-all`이나 다른 사람의 브라우저 종료 명령은 사용하지 않습니다.
