# 클래스 메서드 내부 `반환`이 `ReturnSignal`을 흘려서 값이 에러로 오인 처리됨 — ✅ 해결

## 요약

클래스의 일반 메서드(`init` 제외) 안에서 `반환 <값>;`을 실행하면, 반환값이
`출력` 등 정상 경로로 전달되지 않고 `Interpreter.interpret()`의 최상위
예외 처리로 새어나가 **에러 메시지처럼 취급**된다. 우연히 `str(예외)`가
반환값과 같은 문자열이 되기 때문에 화면에는 그럴듯한 숫자가 찍히지만,
실제로는

- 이후의 모든 문장이 실행되지 않고 스크립트 전체가 중단됨
- CLI/`FileRunner.run_file` 종료 코드가 `1`(에러)이 됨
- 값이 `_stringify()`(예: `42.0` → `42` 트리밍)를 거치지 않아 포맷이 원본 그대로 노출됨

이라는 세 가지 실제 문제가 함께 발생한다.

## 재현 방법

```laugh
클래스 Robot {
    double(n) {
        반환 n * 2;
    }
}
변수 r = Robot();
출력 r.double(21);
출력 "이 줄은 절대 안 보임";
```

`codefab run`(또는 REPL)으로 실행하면:

- **기대**: `42` 출력, 그다음 `이 줄은 절대 안 보임` 출력, 종료 코드 `0`
- **실제**: `42.0` 한 줄만 출력되고 `이 줄은 절대 안 보임`은 출력되지 않음,
  종료 코드 `1`

REPL로 직접 확인한 결과(`codefab/app/repl.py`의 실제 `Repl` 클래스 기준):

```python
Repl(interpreter=create_function_interpreter(), output=out.append).run(iter(lines))
# out == ['> ', '... ', ..., '42.0', '> ']
```

`Interpreter.interpret()`이 반환하는 `InterpretResult`를 직접 찍어보면 더 명확하다:

```python
result = create_function_interpreter().interpret(source)
result.output  # []  — 정상 출력은 비어 있음
result.error   # '42.0'  — 반환값이 "에러 메시지"로 들어가 있음
```

## 원인

1. `반환` 문은 `FunctionExecutorUnit._execute_stmt`에서 내부 제어흐름 신호인
   `ReturnSignal` 예외를 `raise`해서 구현된다.
   (`codefab/function_executor.py:61-65`)
2. 일반 `함수` 호출은 `UserFunction.call()`이 이 `ReturnSignal`을 직접
   `try/except`로 잡아서 값으로 변환한다. (`codefab/function_executor.py:39-43`)
3. 하지만 **클래스 메서드 호출**은 `FunctionExecutorUnit`이 오버라이드하지 않은
   base `ExecutorUnit._call` → `_invoke_function` 경로를 그대로 탄다
   (`codefab/executor_unit.py:403-423`). 이 경로는 `ReturnSignal`의 존재를
   전혀 모르기 때문에 잡지 못하고 그대로 통과시킨다.
4. 결국 `ReturnSignal`이 호출 스택 최상단까지 새어나가
   `Interpreter.interpret()`의 범용 `except Exception`에 걸린다
   (`codefab/interpreter.py:35-36`). 여기서 `error_message = str(exc)`로
   저장되는데, `ReturnSignal.__init__`이 `super().__init__()`을 호출하지
   않아도 `BaseException.__new__`가 생성자 인자를 `.args`에 자동 저장하므로
   `str(ReturnSignal(42.0)) == "42.0"`이 되어, 마치 정상 출력인 것처럼 보인다.
5. 예외가 스크립트 실행 자체를 중단시키므로 이후 문장은 전혀 실행되지 않고,
   `_emit`(`codefab/cli.py:34-40`)은 `result.error is not None`이므로 종료
   코드 `1`을 반환한다.

## 영향 범위

- CLI `run`/`debug` 모드, REPL 모두 동일한 `codefab.function_interpreter.
  create_function_interpreter()` 파이프라인을 쓰므로 세 경로 모두 영향을 받음.
- `init`(생성자)은 원래 `반환` 사용이 금지되어야 하는 대상이라 별개 이슈이며,
  이 버그와는 무관.
- 관련 known-gap 테스트:
  `tests/integration/test_known_gaps_integration.py::test_클래스_메서드_내부에서_반환값을_돌려준다`
  (`xfail(strict=True)`) — 다만 현재 xfail에 적힌 사유
  (`base ExecutorUnit._dispatch_stmt`에 `ReturnStmt` 케이스가 없어
  `UnsupportedStatementError`로 크래시)는 더 이상 실제 실패 원인과 일치하지
  않음(이제는 크래시가 아니라 `ReturnSignal` 누수). 수정 시 xfail 사유 문구도
  같이 갱신 필요.

## 수정 내용

`FunctionExecutorUnit`(`codefab/function_executor.py`)이 `_invoke_function`을
오버라이드해서 `try: return super()._invoke_function(...) / except
ReturnSignal as signal: return signal.value` 형태로 감싸도록 수정. base
`ExecutorUnit._call`이 타는 클래스 메서드/생성자 호출 경로 전체가 이 override를
거치므로, 어디서 호출되든 `ReturnSignal`이 새어나가지 않는다.

수정 후 확인:

- `반환 n * 2;` → `_stringify()`를 거쳐 `42.0`이 아니라 `42`로 정상 출력.
- 반환 뒤 문장(`출력 "이 줄은 절대 안 보임";`)도 계속 실행됨.
- `codefab run`의 종료 코드가 `0`.
- `tests/integration/test_known_gaps_integration.py::test_클래스_메서드_내부에서_반환값을_돌려준다`의
  `xfail(strict=True)`를 제거하고 일반 golden 테스트로 전환.

## 참고

- `docs/미구현기능_및_버그_TODO.md` B1/C3 — 함수 파이프라인 배선 관련
  이전 이력(이번 버그와 인접하지만 다른 문제).
