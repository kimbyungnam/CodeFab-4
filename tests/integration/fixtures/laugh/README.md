# 공유 `.laugh` golden 테스트 fixture

`normal/`, `error/`의 `<이름>.laugh` + `<이름>.out` 쌍은 저장소 루트 `테스트케이스.md`에 정리된
예제를 1:1로 옮긴 것이다. `tests/integration/test_cli_integration.py`가 이 디렉터리를 glob으로
찾아 `python -m codefab.cli <이름>.laugh`를 실행하고, stdout을 `<이름>.out`과 바이트 단위로
비교한다. `normal/`은 종료 코드 0, `error/`는 종료 코드 1을 기대한다.

이 디렉터리는 `cli`가 아니라 `laugh`로 이름 붙였다 — 같은 `.laugh` 소스를 repl/debug 통합
테스트도 함께 참조하기 때문이다. 소비자마다 출력 형태(프롬프트, `[DEBUG]` 로그 등)가 다르므로
소비자별로 별도의 golden 파일을 둔다:

- `<이름>.laugh` — 공유 소스 (필수)
- `<이름>.out` — file-runner golden stdout (필수, 위 설명대로)
- `<이름>.debug.cmds` — debug 명령 스크립트 (선택, 한 줄에 명령 하나: `step`/`next`/
  `continue`/`break <line>` 등). `tests/integration/test_debug_integration.py`가 이 파일이
  있는 케이스만 수집해 `DebugRunner`에 명령을 순서대로 입력하고 캡처한 출력을
  `<이름>.debug.out`과 비교한다. 모든 케이스에 있을 필요는 없고, 대표적인 일부 케이스에만
  추가했다.
- `<이름>.debug.out` — debug golden 출력 (`.debug.cmds`가 있는 케이스에만 함께 둔다)

repl 통합 테스트(`<이름>.repl.out`)는 아직 추가되지 않았다 — 추후 커밋에서 다룬다.

- `normal/` — 테스트케이스.md 1번 섹션(표현식/연산자/진리값, 변수/스코프, 제어 흐름) 24개 예제 +
  3일차 문서 Chapter 3(class) 7개 예제 + Chapter 7(디버그 모드
  `watch`/`unwatch`/`watches`/`inspect`/`breakpoints`/`remove` 명령어) 1개 예제
- `error/` — 테스트케이스.md 2번 섹션(구문 에러, Checker 정적 에러, 런타임 에러) 9개 예제 +
  3일차 문서 Chapter 3(class) 8개 예제

## 에러 메시지 문구 출처

테스트케이스.md의 에러 기대 메시지는 `"~류의 메시지"`로 적혀 있듯 정확한 문자열이 아니라
근사치다. `error/*.out`에는 실제 `codefab/error.py`에 정의된 정확한 메시지를 담았다. 시나리오
자체는 테스트케이스.md와 동일하지만, 문구는 다음과 같이 다르다.

| 테스트케이스.md | 실제 (`codefab/error.py`) |
| --- | --- |
| 식 뒤에 ')'가 필요합니다. | 표현식 뒤에는 ')'가 필요합니다. |
| 잘못된 할당 대상입니다. | 잘못된 대입 대상입니다. |
| 지역 변수는 자기 초기화식에서 읽을 수 없습니다. | 지역 변수 자기 참조 에러입니다. |
| 이미 같은 스코프에 같은 이름의 변수가 있습니다. | 이미 선언된 변수입니다. |
| 식을 기대했습니다. | 아직 처리하지 않는 표현식 종류입니다. |
| 피연산자는 숫자여야 합니다. | 피연산자는 반드시 숫자여야 합니다. |

`값 뒤에 ';'가 필요합니다.`, `정의되지 않은 변수 'notDefined'입니다.`,
`피연산자는 둘 다 숫자이거나 둘 다 문자열이어야 합니다.`는 문구가 그대로 일치한다.

## 케이스 추가

- file-runner: `<normal|error>/<이름>.laugh`와 `<이름>.out` 한 쌍을 추가하면
  `test_cli_integration.py`가 자동으로 수집한다.
- debug: 같은 `<이름>.laugh`에 `<이름>.debug.cmds`와 `<이름>.debug.out`을 추가하면
  `test_debug_integration.py`가 자동으로 수집한다.

파일은 커밋 시 `end-of-file-fixer` pre-commit 훅이 끝에 개행을 강제로 붙이므로, EOF 위치에
의존하는 에러(예: 세미콜론 누락)는 그 개행 때문에 줄 번호가 하나 밀릴 수 있다 — golden 파일은
실제 실행 결과에 맞춰 작성한다.
