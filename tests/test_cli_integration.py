"""codefab CLI(`codefab <file>`) 프로세스 통합 테스트.

테스트케이스.md에 정리된 예제를 실제 파일로 저장한 뒤 `python -m codefab.cli <파일>` 프로세스를
구동해 Assembler -> Checker -> Executor 전체 파이프라인이 올바른 출력/에러 메시지/종료 코드를
내는지 검증한다.

REPL과 달리 CLI(`codefab.cli.Cli.run_file`)는 파일 전체를 한 번에 읽어 `Interpreter.interpret()`에
통째로 넘기므로, 테스트케이스.md의 여러 줄짜리 블록/반복문 예제를 원본 그대로(개행 포함) 사용할 수
있다. 정상 케이스는 종료 코드 0, 에러 케이스는 종료 코드 1을 기대한다.

일부 케이스는 Checker/Assembler의 미구현·버그(`visit_print_stmt`/`visit_if_stmt`/`visit_for_stmt`/
`visit_literal`/`visit_assign`/`visit_logical`/`visit_unary` 부재, `!=` 연산자 미배선, 소수점 리터럴
미지원)로 인해 현재 실패(red)한다 — 알려진 미구현 상태이며, 해당 기능이 구현되면 이 테스트들이
통과해야 한다.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from codefab.error import (
    DuplicateVariableError,
    InvalidAssignmentTargetError,
    InvalidOperandTypeError,
    MismatchedPlusOperandTypeError,
    MissingClosingParenAfterExpressionError,
    MissingSemicolonAfterValueError,
    SelfReferenceInInitializerError,
    UndefinedVariableError,
    UnrecognizedExpressionError,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


def run_cli(source: str, tmp_path: Path) -> subprocess.CompletedProcess:
    script = tmp_path / "script.txt"
    script.write_text(source, encoding="utf-8")
    return subprocess.run(
        [sys.executable, "-m", "codefab.cli", str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
        timeout=10,
    )


NORMAL_CASES = [
    ("산술_우선순위_곱셈", "출력 1 + 2 * 3;", ["7"]),
    ("산술_우선순위_괄호", "출력 (1 + 2) * 3;", ["9"]),
    ("산술_좌결합_뺄셈", "출력 10 - 4 - 3;", ["3"]),
    ("산술_좌결합_나눗셈", "출력 8 / 2 / 2;", ["2"]),
    ("단항_마이너스", "출력 -3 + 2;", ["-1"]),
    ("비교_미만", "출력 1 < 2;", ["참"]),
    ("비교_초과", "출력 3 > 5;", ["거짓"]),
    ("동등성_참", "출력 10 == 10;", ["참"]),
    ("동등성_다름", "출력 10 != 5;", ["참"]),
    ("문자열_연결", '출력 "안녕, " + "말랑!";', ["안녕, 말랑!"]),
    ("정수_출력", "출력 5;", ["5"]),
    ("정수형_실수_출력", "출력 5.0;", ["5"]),
    ("소수_출력", "출력 3.14;", ["3.14"]),
    ("참_리터럴", "출력 참;", ["참"]),
    ("거짓_리터럴", "출력 거짓;", ["거짓"]),
    (
        "변수_선언과_사용",
        "변수 a = 10;\n변수 b = 20;\n출력 a + b;\n",
        ["30"],
    ),
    (
        "변수_재할당",
        "변수 a = 10;\na = a + 5;\n출력 a;\n",
        ["15"],
    ),
    (
        "블록_스코프와_shadowing",
        '변수 x = "전역";\n{\n  변수 x = "안쪽";\n  출력 x;\n}\n출력 x;\n',
        ["안쪽", "전역"],
    ),
    (
        "안쪽_블록에서_바깥_변수_수정",
        "변수 count = 0;\n{\n  count = count + 1;\n}\n출력 count;\n",
        ["1"],
    ),
    (
        "중첩_스코프_해석",
        '변수 outer = "A";\n{\n  변수 inner = "B";\n  {\n    출력 outer + inner;\n  }\n}\n',
        ["AB"],
    ),
    ("만약_참", '만약 (참) 출력 "bbq";', ["bbq"]),
    (
        "만약_아니면",
        '만약 (거짓) 출력 "no"; 아니면 출력 "kfc";',
        ["kfc"],
    ),
    (
        "아니면은_가장_가까운_만약에_결합",
        '만약 (참)\n{\n  만약 (거짓) 출력 "kfc";\n  아니면 출력 "bbq";\n}\n',
        ["bbq"],
    ),
    (
        "반복문",
        "반복 (변수 j = 0; j < 3; j = j + 1) {\n  출력 j;\n}\n",
        ["0", "1", "2"],
    ),
]


@pytest.mark.parametrize(
    "source, expected_output",
    [
        pytest.param(source, expected, id=name)
        for name, source, expected in NORMAL_CASES
    ],
)
def test_정상동작_예제가_기대한_출력을_내고_종료코드_0을_반환한다(
    source, expected_output, tmp_path
):
    result = run_cli(source, tmp_path)

    assert result.stdout.splitlines() == expected_output
    assert result.returncode == 0


ERROR_CASES = [
    (
        "세미콜론_누락",
        "출력 1 + 2",
        str(MissingSemicolonAfterValueError(line=1)),
    ),
    (
        "닫는_괄호_누락",
        "출력 (1 + 2;",
        str(MissingClosingParenAfterExpressionError(line=1)),
    ),
    (
        "잘못된_할당_대상",
        "변수 a = 1;\n변수 b = 2;\na + b = 3;\n",
        str(InvalidAssignmentTargetError(line=3)),
    ),
    (
        "표현식_자리에_잘못된_토큰",
        "출력 * 5;",
        str(UnrecognizedExpressionError()),
    ),
    (
        "지역_변수_자기_초기화식에서_읽기",
        "{\n  변수 a = a;\n}\n",
        str(SelfReferenceInInitializerError(line=2)),
    ),
    (
        "같은_스코프_중복_선언",
        '{\n  변수 a = "hi";\n  변수 a = 3;\n}\n',
        str(DuplicateVariableError(line=3)),
    ),
    (
        "정의되지_않은_변수_참조",
        "출력 notDefined;",
        str(UndefinedVariableError("notDefined", line=1)),
    ),
    (
        "덧셈에_숫자와_문자열_혼용",
        '출력 1 + "HI";',
        str(MismatchedPlusOperandTypeError(line=1)),
    ),
    (
        "숫자가_아닌_값에_단항_마이너스",
        '출력 -"말랑";',
        str(InvalidOperandTypeError(line=1)),
    ),
]


@pytest.mark.parametrize(
    "source, expected_error",
    [pytest.param(source, expected, id=name) for name, source, expected in ERROR_CASES],
)
def test_에러_예제가_기대한_에러_메시지를_내고_종료코드_1을_반환한다(
    source, expected_error, tmp_path
):
    result = run_cli(source, tmp_path)

    assert expected_error in result.stdout.splitlines()
    assert result.returncode == 1


def test_존재하지_않는_파일이면_파일_오류_메시지를_내고_종료코드_1을_반환한다(tmp_path):
    missing = tmp_path / "없는파일.txt"

    result = subprocess.run(
        [sys.executable, "-m", "codefab.cli", str(missing)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
        timeout=10,
    )

    assert "파일 오류" in result.stdout
    assert result.returncode == 1
