# GitHub 협업 Best Practice 사례

이 문서는 CodeFab-4 저장소의 Issue / PR / 리뷰 코멘트를 훑어보고, 앞으로도 참고할 만한 협업
패턴을 모아둔 것입니다. 각 항목은 실제 사례(번호, 링크)를 근거로 합니다.

## 1. 코드 리뷰가 실제 결함/스코프 크리프를 잡아낸 사례

### 통합 누락(wiring gap) 발견 — [PR #65](https://github.com/kimbyungnam/CodeFab-4/pull/65)
`가져오기` 문법을 Assembler 레벨에서만 구현한 PR에서, 리뷰어(kimbyungnam)가 실제로
`Interpreter().interpret('가져오기 "sum.txt" 별칭 sum;')`을 실행해보고
`Checker`에 `visit_import_stmt`가 없어 런타임 에러가 난다는 점을 짚었습니다. 작성자는
"이번 PR은 파싱까지만, Checker/Executor는 다음 PR에서 순차 연결"이라고 명확히 스코프를
답변했습니다. → **테스트가 파서 결과만 검증하고 있으면 파이프라인 전체가 동작한다는 보장이
안 된다**는 것을 보여주는 사례이며, `docs/함수_클래스_배열_가져오기_테스트.md`와
CLAUDE.md의 "함수는 기본 파이프라인에 배선되지 않았다" 경고와 같은 패턴입니다.

### YAGNI/스코프 초과 구현 제거 — [PR #66](https://github.com/kimbyungnam/CodeFab-4/pull/66)
리뷰어가 클래스 Executor 테스트에 `Callable` 확인 로직이 있는 걸 보고 "이건 함수 요구사항인데
클래스에 왜 추가되었나요?"라고 질문했고, 작성자가 "요구사항에 없는 불필요한 구현이었다"며
바로 제거했습니다. → 요구사항 밖 구현은 발견 즉시 삭제하는 문화.

### 구체적 재현 스텝을 포함한 변경 요청 — [PR #69](https://github.com/kimbyungnam/CodeFab-4/pull/69)
`hasuplee`가 CHANGES_REQUESTED를 남기며 어떤 부분(`line_of_expr`)이 어떤 입력
(`arr[0] = 10;` 같은 배열 인덱스 라인)에서 실패하는지 코드 스니펫으로 정확히 짚었고,
작성자가 즉시 반영 → APPROVED로 이어졌습니다. → **"무엇이 왜 틀렸는지 + 재현 예시"**가
포함된 리뷰 코멘트는 왕복 없이 한 번에 수정으로 이어짐.

### 알려진 한계(known gap)를 승인하면서도 명시 — [PR #71](https://github.com/kimbyungnam/CodeFab-4/pull/71)
Resolver/Optimizer PR 리뷰에서 `hasuplee`는 구현 품질(기존 스코프 구조 재사용, distance 조회
실패 시 동적 조회로 폴백하는 안전장치, `mocker.spy`로 실제 스코프 조회가 안 일어났는지까지
검증한 테스트)을 구체적으로 칭찬하면서도, "`create_optimized_interpreter()`가 아직
`cli.py`/`repl.py`에는 연결되어 있지 않다"는 점을 승인 코멘트에 남겼습니다. →
**승인하더라도 알려진 한계는 기록해 다음 작업으로 넘긴다**. (실제로 이 상태는 지금도
그대로이며 README 체크리스트에도 반영했습니다.)

### 구체적인 구현 방향까지 제시하는 리뷰 — [PR #72](https://github.com/kimbyungnam/CodeFab-4/pull/72)
같은 블록 안에서 동일 파일을 다시 `가져오기` 해도 통과되는 버그를, kimbyungnam이 "스택 자료구조
하나 추가 → block 진입/탈출 시 push/pop → visit_import_stmt에서 검사"까지 단계별로 제안하고
별도 에러 클래스명까지 제안했습니다. → 리뷰가 단순 지적을 넘어 실행 가능한 설계안을 제공.

## 2. 이슈 → PR 추적성이 잘 지켜진 사례

- [Issue #48 "Checker 구현"](https://github.com/kimbyungnam/CodeFab-4/issues/48) → 코멘트에서
  "[#49](https://github.com/kimbyungnam/CodeFab-4/pull/49)로 수정하였습니다"로 해결 PR을 명시.
- [Issue #44 "error 통합 모듈 건"](https://github.com/kimbyungnam/CodeFab-4/issues/44) → 코멘트로
  "ParseError는 반영이 안 됐다", "assembler/errors.py도 수정 필요"를 주고받은 뒤
  [PR #45](https://github.com/kimbyungnam/CodeFab-4/pull/45) "refactor: error 모듈 통합"으로 해결.
- [Issue #56 "3일차 작업 배분"](https://github.com/kimbyungnam/CodeFab-4/issues/56)처럼 기능 이슈가
  아니라 **작업 분배용 이슈**를 만들어 두는 패턴도 있음 — 코드 변경 없는 조율에도 이슈를 활용.

## 3. 알려진 한계를 테스트로 문서화 — [PR #91](https://github.com/kimbyungnam/CodeFab-4/pull/91)
"함수 미배선과 메서드 return 크래시를 known gap으로 문서화"라는 제목 그대로, 고치지 않은 버그를
그냥 방치하는 대신 **실패를 재현하는 테스트를 추가해 "여기 문제가 있다"를 코드로 남겨두는 방식**을
택했습니다. 이런 갭은 이후 [Issue #93](https://github.com/kimbyungnam/CodeFab-4/issues/93)
(`print(a, b)` 다중 값 미지원)처럼 이슈로도 별도 등록되어 열려 있는 상태로 추적됩니다.

## 4. 설계 트레이드오프를 코멘트로 남긴 사례 — [PR #64](https://github.com/kimbyungnam/CodeFab-4/pull/64)
CLI 진입점을 하나로 통합하는 PR에서 리뷰어가 "`codefab <경로>`처럼 인자 유무로 파일 모드를
판단하면 어떨까요?"라고 제안했고, 작성자는 "이후 `codefab debug <경로>`가 추가되면 `debug`라는
단어 자체가 파일 경로로 오인될 수 있어(`path="debug"`), 서브커맨드로 모드를 명시하는 구조를
유지했다"고 구체적 근거를 들어 답변했습니다. → **왜 그렇게 설계했는지 이유를 코멘트에 남기면**,
나중에 같은 질문이 반복되지 않음(실제로 `debug` 서브커맨드는 이후 PR #69에서 추가됨).

## 5. 문서 리뷰도 코드 리뷰만큼 꼼꼼하게 — [PR #78](https://github.com/kimbyungnam/CodeFab-4/pull/78)
README 리팩터링 PR에서 kimbyungnam이 "Quick Start랑 Install 부분이 겹치는 것 같습니다"라고
CHANGES_REQUESTED를 남겼고, 이후 hasuplee가 병합 후 "충돌 마커 없이 정리됐고 527개 테스트 전부
통과, README 내용도 실제 구현과 정확히 일치한다"까지 재검증하고 승인했습니다. → 문서 PR도
"내용이 실제 구현과 일치하는지"까지 검증 대상으로 삼음.

## 요약: 재사용할 만한 패턴

1. 리뷰할 때 **실제로 실행해서** 파이프라인 전체가 동작하는지 확인한다 (PR #65).
2. 요구사항에 없는 구현은 발견 즉시 제거한다 (PR #66).
3. 변경 요청 코멘트에는 **재현 코드/예시**를 포함한다 (PR #69).
4. 승인하더라도 **알려진 한계는 명시적으로 남긴다** (PR #71) — 필요하면 실패 테스트로 남긴다 (PR #91).
5. 설계 결정에는 **이유**를 코멘트로 남긴다 (PR #64).
6. 이슈는 버그/기능뿐 아니라 **작업 배분**에도 쓰고, 해결 PR 번호를 코멘트로 연결해 추적성을
   유지한다 (#48, #44, #56).
