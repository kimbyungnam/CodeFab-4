"""알려진 기능 격차(known gap)를 문서화하는 CLI 통합 테스트.

3일차 문서에서 요구하지만 실제 codefab.cli 파이프라인에서는 아직 제대로 동작하지 않는
것으로 확인된 동작들을 `xfail(strict=True)`로 모아 문서화한다. 각 테스트는 *바라는*
최종 동작을 assert한다 — 지금은 실패해야 정상이고, 관련 기능이 고쳐지는 날 XPASS로
뒤집혀 실제 golden 테스트로 교체하라는 신호가 된다.

## Function (Ch.2) 파이프라인 배선 — ✅ 해결 (`feature/wire-function-pipeline`)

`함수`/`Func` 기능이 `codefab.cli`/`codefab/app/repl.py`/`codefab/app/debug.py`가 쓰는
파이프라인에 배선되어(`docs/미구현기능_및_버그_TODO.md` B1 참고) 아래 테스트들은 더 이상
xfail이 아니라 일반 golden 테스트로 동작한다.

## 클래스 메서드 내부 return (base 파이프라인 버그)

클래스(Ch.3)는 base 파이프라인에 배선돼 있지만, `init`이 아닌 일반 메서드 안에서
`반환 <값>;`을 쓰면 값을 반환하는 대신 크래시한다. `_invoke_function`이 메서드 본문을
`_execute_block`으로 실행하는데, base `ExecutorUnit._dispatch_stmt`에 `ReturnStmt` 케이스가
없어 `UnsupportedStatementError: 지원하지 않는 Statement입니다: 'ReturnStmt'`가 발생한다.
Chapter 3 자체 예제는 메서드에서 값을 반환하지 않아 이 버그를 밟지 않으므로,
`fixtures/laugh/normal/`의 정상 클래스 golden fixture에서는 드러나지 않는다.
"""

import pytest

from tests.integration.test_cli_integration import run_cli

_METHOD_RETURN_XFAIL_REASON = (
    "일반 메서드 내부의 '반환 <값>;'이 base ExecutorUnit._dispatch_stmt에"
    " ReturnStmt 케이스가 없어 UnsupportedStatementError로 크래시함"
)


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


@pytest.mark.xfail(strict=True, reason=_METHOD_RETURN_XFAIL_REASON)
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
