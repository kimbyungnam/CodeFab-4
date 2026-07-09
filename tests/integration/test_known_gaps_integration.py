"""알려진 기능 격차(known gap)를 문서화하는 CLI 통합 테스트.

3일차 문서에서 요구하지만 실제 codefab.cli 파이프라인에서는 아직 제대로 동작하지 않는
것으로 확인된 동작들을 `xfail(strict=True)`로 모아 문서화한다. 각 테스트는 *바라는*
최종 동작을 assert한다 — 지금은 실패해야 정상이고, 관련 기능이 고쳐지는 날 XPASS로
뒤집혀 실제 golden 테스트로 교체하라는 신호가 된다.

## Function (Ch.2) 파이프라인 배선 — ✅ 해결 (`feature/wire-function-pipeline`)

`함수`/`Func` 기능이 `codefab.cli`/`codefab/app/repl.py`/`codefab/app/debug.py`가 쓰는
파이프라인에 배선되어(`docs/미구현기능_및_버그_TODO.md` B1 참고) 아래 테스트들은 더 이상
xfail이 아니라 일반 golden 테스트로 동작한다.

## 클래스 메서드 내부 return의 ReturnSignal 누수 — ✅ 해결

클래스(Ch.3)는 base 파이프라인에 배선돼 있었지만, `init`이 아닌 일반 메서드 안에서
`반환 <값>;`을 쓰면 `FunctionExecutorUnit._execute_stmt`가 던지는 내부 제어흐름 신호
`ReturnSignal`이 base `ExecutorUnit._call`/`_invoke_function` 경로(클래스 메서드 호출)에서는
잡히지 않고 `Interpreter.interpret()`까지 새어나가 반환값이 에러로 오인 처리됐다
(우연히 `str(ReturnSignal)`이 반환값과 같아 화면에는 값처럼 보였지만, 이후 문장이 전혀
실행되지 않고 종료 코드도 1이었음). `FunctionExecutorUnit`이 `_invoke_function`도
오버라이드해 `ReturnSignal`을 잡도록 수정해 해결.
"""

from tests.integration.test_cli_integration import run_cli


def test_함수_선언과_호출_매개변수_전달(tmp_path):
    script = tmp_path / "main.laugh"
    script.write_text(
        "함수 add(a, b) {\n    반환 a + b;\n}\n변수 ret = add(3, 7);\n출력 ret;\n",
        encoding="utf-8",
    )

    result = run_cli(script, cwd=tmp_path)

    assert result.stdout == "10\n"
    assert result.returncode == 0


def test_반환값_없는_return은_null을_반환한다(tmp_path):
    script = tmp_path / "main.laugh"
    script.write_text(
        "함수 no_value() {\n    반환;\n}\n변수 ret = no_value();\n출력 ret;\n",
        encoding="utf-8",
    )

    result = run_cli(script, cwd=tmp_path)

    assert result.stdout == "None\n"
    assert result.returncode == 0


def test_재귀_호출로_팩토리얼을_계산한다(tmp_path):
    script = tmp_path / "main.laugh"
    script.write_text(
        "함수 fact(n) {\n"
        "    만약 (n <= 1) 반환 1;\n"
        "    반환 n * fact(n - 1);\n"
        "}\n"
        "변수 result = fact(5);\n"
        "출력 result;\n",
        encoding="utf-8",
    )

    result = run_cli(script, cwd=tmp_path)

    assert result.stdout == "120\n"
    assert result.returncode == 0


def test_클래스_메서드_내부에서_반환값을_돌려준다(tmp_path):
    script = tmp_path / "main.laugh"
    script.write_text(
        "클래스 Robot {\n"
        "    double(n) {\n"
        "        반환 n * 2;\n"
        "    }\n"
        "}\n"
        "변수 r = Robot();\n"
        "출력 r.double(21);\n",
        encoding="utf-8",
    )

    result = run_cli(script, cwd=tmp_path)

    assert result.stdout == "42\n"
    assert result.returncode == 0
