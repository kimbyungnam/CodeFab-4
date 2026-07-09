# 미구현 기능 및 버그 — 작업 목록 (Task Backlog)

> `docs/reference/1일차_CodeFab_Interpreter.md`, `docs/reference/3일차_CodeFab_Interpreter.md`
> 요구사항과 현재 코드베이스(`codefab/`)를 비교해 발견한 **미구현 기능**과 **버그**를
> 작업 항목으로 정리한 문서. 각 항목은 근거(파일/라인)와 재현 방법을 포함한다.
>
> 조사 시점 기준(브랜치 `test/laugh-repl-fixtures`)이며, `CLAUDE.md`의 "StatementParser는
> Protocol/테스트 더블일 뿐 실제 statement 파서 미구현"이라는 설명은 **이미 낡은 정보**다 —
> `codefab/assembler/statement_parser.py`가 실제로 구현되어 있으며, `CLAUDE.md`는 별도로
> 갱신이 필요하다.

## 요약

기능 자체(함수, 클래스, 배열, 정적 바인딩, 상수 폴딩)는 각각 구현되어 있고, **세 개의 서로
다른 파이프라인**(`Interpreter`(base) / `create_function_interpreter()` /
`create_optimized_interpreter()`)으로 나뉘어 있다. `create_optimized_interpreter()`가
`feature/optimizing_connect`에서 함수/클래스/배열/import를 모두 지원하는 단일 파이프라인으로
통합되었고, CLI·REPL·debug 셸은 모두 이 파이프라인을 기본값으로 사용하도록 배선되어 있어
**함수·클래스·배열·import·정적 바인딩/상수 폴딩 모두 실제 사용자 경로(REPL/`run`/`debug`)에서
정상 동작한다.** 이번 PR에서는 `Optimizer`의 상수 폴딩이 함수/메서드 본문과 호출식 인자까지
재귀하도록 확장해 마지막 남은 gap(B2)을 닫았다.

---

## A. Day-1 기준 미구현/미흡 사항

### A1. REPL이 여러 줄에 걸친 문장(블록/반복문/if-else)을 실행하지 못함
- **파일**: `codefab/app/repl.py` `main()` (48~53행)
- **증상**: `sys.stdin`을 한 줄 단위로 읽어 `Interpreter.interpret()`에 즉시 넘기므로,
  `반복 (...) {` 뒤에 body와 `}`가 다음 줄에 오는 입력은 모두
  `블록은 '}'로 닫아야 합니다.` 에러로 실패한다.
- **재현/증거**: `pytest tests -q` 실행 시 `tests/integration/test_repl_integration.py`의
  7개 테스트 실패 (`반복문`, `블록_스코프와_shadowing`,
  `아니면은_가장_가까운_만약에_결합`, `중첩_스코프_해석`,
  `안쪽_블록에서_바깥_변수_수정` 외 에러 golden 2건). 해당 테스트 파일 docstring(20~24행)에
  이미 "red" 상태로 알려진 이슈로 문서화되어 있음 — 아직 미해결.
- **작업**: REPL 입력을 줄 단위가 아니라, 괄호/중괄호 깊이를 추적해 문장이 완결될
  때까지 버퍼링한 뒤 Assembler에 넘기도록 수정.

### A2. README.md가 실제 언어 기능을 문서화하지 않음
- **근거**: 3일차 문서 Chapter 8, "Custom Language 사용 방법을 README.md에 명시"
  요구사항 대비, 현재 `README.md` 38~55행은 REPL과 `run` 모드만 설명하며 `class`/`This`/
  `Super`/`instanceof`, `Array`, `import`, 함수, `debug` CLI 서브커맨드에 대한 언급이 없음.
- **작업**: README.md에 클래스, 배열, import, 함수, debug 모드 사용법 섹션 추가.

---

## B. Day-3 기준 미구현 사항 (주로 "파이프라인 통합" 문제)

### B1. [최우선] 함수(Func/함수) 기능이 CLI/REPL/debug 경로에서 전혀 동작하지 않음 — ✅ 해결 (`feature/wire-function-pipeline`)
- **근거**: `codefab/cli.py` `main()` (56~62행), `codefab/app/repl.py` `main()` (48~53행),
  `codefab/app/debug.py` `DebugRunner.run_file` (250~251행, `Assembler()`/`Checker()` 하드코딩)
  모두 base `Interpreter()`/`Assembler()`/`Checker()`를 사용하고, 함수 지원 파이프라인인
  `create_function_interpreter()`(`codefab/function_interpreter.py`)는 어디에서도 호출되지 않음.
- **결과**: base `StatementParser`에 `TokenType.FUN`/`RETURN` 케이스가 없고
  `ExecutorUnit._dispatch_stmt`에도 `FunctionStmt`/`ReturnStmt` 케이스가 없어서, 사용자가
  실제로 실행하는 세 가지 모드(REPL/run/debug) 어디서도 `함수` 선언을 파싱조차 할 수 없음.
- **작업**: CLI/REPL/debug 모두 `create_function_interpreter()`(또는 함수+최적화+클래스를
  모두 합친 단일 파이프라인)를 사용하도록 배선 변경. 최소한 옵션 플래그로라도 함수 실행이
  가능해야 함.
- **남은 한계**: debug 모드에서 `함수` 선언 줄이나 `반환` 문 줄에는 breakpoint가 걸리지
  않음 — `FunctionExecutorUnit._execute_stmt`가 이 두 statement에 대해 `super()`를 호출하지
  않고 조기 반환해 `_before_stmt` 훅(`executor_unit.py` `_execute_stmt`, 206~207행)을 거치지
  않기 때문. 실행 결과 자체는 정확하며, 별도 후속 작업으로 남겨둠.

### B2. 정적 바인딩(static binding) / 상수 폴딩 최적화가 CLI/REPL/debug에서 사용 불가 — ✅ 해결
- **확인 (2026-07-09)**: `feature/optimizing_connect`에서 `create_optimized_interpreter()`가
  `OptimizingChecker(Resolver, FunctionChecker)` + `OptimizedFunctionExecutorUnit
  (OptimizedExecutorUnit, FunctionExecutorUnit)` + `FunctionAssembler`로 함수/클래스/배열/
  import까지 모두 지원하는 단일 파이프라인이 되었고, `cli.py`/`repl.py`/`debug.py`가 이
  파이프라인을 기본값으로 사용하도록 배선됨. 이 PR에서는 `Optimizer`가 함수/메서드 본문과
  호출식 인자까지 상수 폴딩을 재귀하도록 확장해 마지막 남은 gap을 닫았다.

### B3. CLI에 파이프라인 선택 옵션이 없음 — ✅ 해결 (B2에 흡수)
- **확인 (2026-07-09)**: B2 해결로 `create_optimized_interpreter()`가 함수/클래스/배열/
  최적화를 모두 포함하는 단일 파이프라인이자 CLI/REPL/debug의 기본 경로가 되어, 별도
  `--optimize`/`--functions` 플래그 없이도 구현된 모든 기능에 접근 가능해졌다. 통합 방향이
  "단일 기본 파이프라인"이었으므로 이 항목은 B2에 흡수되어 별도 작업이 필요 없다.

### B4. 생성자(`init`)에서 `return` 사용 금지 검사 미구현
- **근거**: 3일차 문서 Chapter 3 "클래스 관련 오류검사" — `init() { return 5; }` 에러 케이스.
  `codefab/error.py`에 해당 에러 클래스가 없고, 어떤 Checker에도 `init` 내부 `return`을
  막는 로직이 없음.
- **작업**: 클래스 checker에 `init` 메서드 본문 내 `return` 사용 감지 및 전용 에러 추가.

---

## C. 확인된 버그 (재현 완료)

### C1. 호출 불가능한 대상 호출 시 조용히 무시됨 (에러 미발생)
- **파일**: `codefab/executor_unit.py` `_call` (388~399행)
- **버그**: `LaughClass`/`LaughFunction` 외의 값(예: 문자열)을 호출하면 아무 예외 없이
  `None`을 반환하고 넘어감.
- **재현**:
  ```
  변수 x = "hello"; x(); 출력 "이 줄까지 실행되면 버그";
  ```
  → 위 출력문이 실행됨. 3일차 문서 요구사항(`var x = "hello"; x();` → 에러)과 어긋남.
  (`NotCallableError`는 `function_executor.py`에만 존재하고 B1 문제로 인해 CLI/REPL/debug에서
  도달 불가능한 코드임.)
- **작업**: base `ExecutorUnit._call`에도 호출 불가 대상에 대해 에러를 발생시키도록 수정
  (혹은 B1 해결 후 함수 파이프라인의 `NotCallableError` 경로로 통합).

### C2. `FunctionExecutorUnit`이 클래스 인스턴스화를 깨뜨림 — ✅ 해결 (`refactoring/function-executor-call-delegation`)
- **파일**: `codefab/function_executor.py` `_evaluate_call` (75~87행)
- **버그**: `ExecutorUnit._evaluate_call`을 완전히 대체하면서 `UserFunction`이 아닌 모든
  대상(클래스 포함)에 대해 `NotCallableError`를 발생시킴.
- **재현** (`create_function_interpreter()` 경로):
  ```
  클래스 Robot { move(dist) { 나.position = 나.position + dist; } }
  변수 r = Robot();
  ```
  → `[7번째 줄] 호출 가능한 대상(함수)이 아닙니다.` 에러 발생.
- **작업**: `_evaluate_call`이 `LaughClass` 인스턴스화 케이스를 `super()` 호출로 위임하도록 수정.

### C3. 클래스 메서드 내부의 `return`이 "함수 외부" 에러로 잘못 처리됨 — ✅ 해결 (`refactoring/function-checker-method-depth`)
- **파일**: `codefab/checker.py` `visit_class_stmt` (148~164행),
  `codefab/function_checker.py` `visit_return_stmt` (50~52행)
- **버그**: `visit_class_stmt`가 메서드 본문마다 `self.scopes`는 push/pop 하지만
  `self.function_depth`는 건드리지 않음. `FunctionChecker.visit_return_stmt`는
  `function_depth == 0`일 때만 검사하므로 모든 메서드의 `return`이 "함수 외부" 에러로 처리됨.
- **재현** (`create_function_interpreter()` 경로):
  ```
  클래스 Robot { move() { 반환 1; } }
  ```
  → `[4번째 줄] 함수 외부에서는 '반환'을 사용할 수 없습니다.` (스펙상 `init`만 return 금지,
  일반 메서드의 return은 허용되어야 함 — B4와 연관)
- **작업**: `visit_class_stmt`가 메서드 진입 시 `function_depth`도 증가/감소시키도록 수정.

### C4. 클래스 메서드 내부 import의 중복-import 검사가 형제 스코프 규칙을 어김
- **파일**: `codefab/checker.py` `visit_class_stmt` (158~163행) vs `visit_block_stmt` (68~76행)
- **버그**: `visit_class_stmt`는 메서드마다 `self.scopes.append(set())`만 하고
  `self.imported_paths`는 push/pop하지 않아 두 스택이 어긋남 (`visit_block_stmt`는 둘 다
  동기화함).
- **재현**:
  ```
  클래스 Robot {
      move()  { 가져오기 "x.txt" 별칭 x; }
      other() { 가져오기 "x.txt" 별칭 x2; }
  }
  ```
  → `DuplicateImportError: [6번째 줄] 이미 가져온 파일입니다: 'x.txt'` 발생.
  형제 스코프(서로 다른 메서드)는 같은 파일을 각자 import할 수 있어야 함 — 동일 규칙이
  형제 `BlockStmt`에 대해서는 `test_checker.py::test_서로_다른_형제_스코프에서는_같은_파일_재_import_허용`로
  이미 올바르게 테스트되어 있음. 또한 import 기록이 바깥 스코프의 `imported_paths[0]`에
  영구적으로 새어 나감.
- **작업**: `visit_class_stmt`에서 메서드 진입/이탈 시 `imported_paths`도 `visit_block_stmt`와
  동일하게 push/pop 하도록 수정.

### C6. 클래스 메서드 내부 `반환`의 `ReturnSignal`이 호출 스택 최상단까지 새어나감 — ✅ 해결
- **파일**: `codefab/function_executor.py` `_invoke_function` (신규 override),
  `codefab/executor_unit.py` `_invoke_function` (416~423행)
- **버그**: C3가 checker 단계(`function_depth`)는 고쳤지만, 실행 단계에서는 여전히
  일반 메서드 호출이 base `ExecutorUnit._call`/`_invoke_function` 경로를 타고, 이 경로는
  `FunctionExecutorUnit`이 `반환`을 구현하는 내부 신호 `ReturnSignal`을 모르기 때문에
  잡지 못하고 그대로 통과시킴. 결과적으로 `ReturnSignal`이 `Interpreter.interpret()`의
  범용 `except Exception`까지 새어나가 반환값이 **에러로 오인 처리**됨 — 우연히
  `str(ReturnSignal)`이 반환값과 같은 문자열이라 화면에는 그럴듯한 값처럼 보이지만, 실제로는
  이후 문장이 전혀 실행되지 않고 종료 코드도 `1`이 됨. `_stringify()`도 거치지 않아
  `42.0`처럼 원본 포맷 그대로 노출됨.
- **재현**: `docs/issue-class-method-return-signal-leak.md` 참고.
- **작업**: `FunctionExecutorUnit`이 `_invoke_function`도 오버라이드해서 `ReturnSignal`을
  잡아 값으로 변환하도록 수정 (`feature/wire-function-pipeline`).

### C5. 에러 메시지 문구가 문서에 명시된 정확한 한국어 문구와 다름
- **파일**: `codefab/error.py`
  - `DuplicateVariableError` (37~39행): 현재 `"이미 선언된 변수입니다."` — 1일차 문서(및
    `CLAUDE.md`가 인용하는 팀 지정 메시지)는
    `"이미 해당 변수는 현재 스코프에서 사용중입니다."`.
  - `SelfReferenceInInitializerError` (42~44행): 현재 `"지역 변수 자기 참조 에러입니다."` —
    문서 문구는 `"자신의 초기화식에서 지역변수를 읽을 수 없습니다."`.
  - 그 외 `InvalidOperandTypeError`/`DivisionByZeroError` 등도 어미가 문서 원문(`"~한다"`)과
    다소 다름(`"~합니다"`) — 우선순위 낮은 cosmetic 이슈.
- **작업**: 팀에서 어느 문구를 기준으로 삼을지 정한 뒤 (a) 에러 메시지 통일 또는
  (b) 문서/`CLAUDE.md` 쪽 인용 문구 갱신 중 택일. 정확한 문구를 검증하는 테스트가 있다면
  같이 갱신.

---

## 버그 아님 (참고용, 작업 불필요)

- `ForStmt`가 `init`/`condition`/`increment`를 감싸는 자체 스코프 없이 바깥 환경을
  공유하고 `body` 블록에만 새 스코프를 만드는 것은 `checker.py`/`executor_unit.py` 양쪽에서
  일관되며 `tests/test_resolver.py` docstring에도 의도된 설계로 명시되어 있음.
- import 스코프 규칙(함수/클래스 선언 import 금지, var + 중첩 import만 허용)은
  `CLAUDE.md`에 문서화된 팀의 스코프 결정과 일치하며 `codefab/module_loader.py`
  `_validate_declarations_only` (46행)로 잘 구현·테스트되어 있음
  (`tests/test_module_loader.py`, `tests/test_import_integration.py`).

---

## 우선순위 제안

1. **B1 + B2 + C1/C2/C3** — 함수/클래스/최적화 파이프라인 통합 (현재 사용자가 실제로
   함수를 쓸 방법이 없다는 게 가장 심각한 문제)
2. **A1** — REPL 멀티라인 입력 처리 (통합 테스트 7건 실패 중)
3. **C4** — 클래스 메서드 import 스코프 버그
4. **B4** — init 내부 return 금지 검사
5. **C5, A2, B3** — 메시지 문구 정합성, 문서화, CLI 옵션 정리
