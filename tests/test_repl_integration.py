"""codefab-repl 프로세스 통합 테스트.

테스트케이스.md에 정리된 예제를 실제 `python -m codefab.app.repl` 프로세스에 stdin으로
넣어 Assembler -> Checker -> Executor 전체 파이프라인이 올바른 출력/에러 메시지를 내는지
검증한다.

REPL(`codefab.app.repl.main`)은 stdin을 한 줄씩 읽어 줄마다 별도로 `Interpreter.interpret()`를
호출하므로, 원본 문서의 여러 줄짜리 블록/반복문 예제는 개행을 제거하고 한 줄로 합쳐서 입력한다.
또한 `main()`은 파이프라인 에러가 나도 항상 종료 코드 0을 반환하므로 exit code는 검증하지 않는다.

일부 케이스는 Checker에 `visit_print_stmt`/`visit_if_stmt`/`visit_for_stmt`/`visit_literal`이
아직 구현되어 있지 않아 현재 실패(red)한다 — 이는 알려진 미구현 상태이며, 해당 기능이 구현되면
이 테스트들이 통과해야 한다.
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
PROMPT_LINE = "> "
CONTINUATION_PROMPT_LINE = "... "


def run_repl(source: str) -> list[str]:
    result = subprocess.run(
        [sys.executable, "-m", "codefab.app.repl"],
        input=source if source.endswith("\n") else source + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
        timeout=10,
    )
    # 프롬프트는 줄바꿈 없이 다음 출력과 같은 줄에 이어붙어 나오므로(REPL 모드 스펙),
    # 프롬프트 문자열을 전부 제거한 뒤 실제 출력 줄만 남긴다.
    output = result.stdout.replace(PROMPT_LINE, "").replace(
        CONTINUATION_PROMPT_LINE, ""
    )
    return [line for line in output.splitlines() if line]


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
        "변수 a = 10; 변수 b = 20; 출력 a + b;",
        ["30"],
    ),
    (
        "변수_재할당",
        "변수 a = 10; a = a + 5; 출력 a;",
        ["15"],
    ),
    (
        "블록_스코프와_shadowing",
        '변수 x = "전역"; { 변수 x = "안쪽"; 출력 x; } 출력 x;',
        ["안쪽", "전역"],
    ),
    (
        "안쪽_블록에서_바깥_변수_수정",
        "변수 count = 0; { count = count + 1; } 출력 count;",
        ["1"],
    ),
    (
        "중첩_스코프_해석",
        '변수 outer = "A"; { 변수 inner = "B"; { 출력 outer + inner; } }',
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
        '만약 (참) { 만약 (거짓) 출력 "kfc"; 아니면 출력 "bbq"; }',
        ["bbq"],
    ),
    (
        "반복문",
        "반복 (변수 j = 0; j < 3; j = j + 1) { 출력 j; }",
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
def test_정상동작_예제가_기대한_출력을_낸다(source, expected_output):
    assert run_repl(source) == expected_output


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
        "변수 a = 1; 변수 b = 2; a + b = 3;",
        str(InvalidAssignmentTargetError(line=1)),
    ),
    (
        "표현식_자리에_잘못된_토큰",
        "출력 * 5;",
        str(UnrecognizedExpressionError(line=1)),
    ),
    (
        "지역_변수_자기_초기화식에서_읽기",
        "{ 변수 a = a; }",
        str(SelfReferenceInInitializerError(line=1)),
    ),
    (
        "같은_스코프_중복_선언",
        '{ 변수 a = "hi"; 변수 a = 3; }',
        str(DuplicateVariableError(line=1)),
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
def test_에러_예제가_기대한_에러_메시지를_낸다(source, expected_error):
    assert expected_error in run_repl(source)
