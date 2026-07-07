import pytest

from codefab.ast_nodes import (
    Assign,
    Binary,
    BlockStmt,
    ExpressionStmt,
    ForStmt,
    Grouping,
    IfStmt,
    Literal,
    PrintStmt,
    Unary,
    Variable,
    VarStmt,
)
from codefab.executor_unit import ExecutorRuntimeError, ExecutorUnit
from codefab.tokens import Token, TokenType

OPERATOR_TOKEN_TYPES = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    ">": TokenType.GREATER,
    ">=": TokenType.GREATER_EQUAL,
    "<": TokenType.LESS,
    "<=": TokenType.LESS_EQUAL,
    "==": TokenType.EQUAL_EQUAL,
    "!=": TokenType.BANG_EQUAL,
}


def make_operator_token(lexeme: str, line: int = 1) -> Token:
    return Token(
        type=OPERATOR_TOKEN_TYPES[lexeme], lexeme=lexeme, literal=None, line=line
    )


def make_identifier_token(lexeme: str, line: int = 1) -> Token:
    return Token(type=TokenType.IDENTIFIER, lexeme=lexeme, literal=None, line=line)


def make_binary(left, operator_lexeme: str, right) -> Binary:
    return Binary(left=left, operator=make_operator_token(operator_lexeme), right=right)


def make_unary(right, operator_lexeme: str = "-") -> Unary:
    return Unary(operator=make_operator_token(operator_lexeme), right=right)


def make_variable(name_lexeme: str) -> Variable:
    return Variable(name=make_identifier_token(name_lexeme))


def make_var_stmt(name_lexeme: str, initializer) -> VarStmt:
    return VarStmt(name=make_identifier_token(name_lexeme), initializer=initializer)


def make_assign(name_lexeme: str, value) -> Assign:
    return Assign(name=make_identifier_token(name_lexeme), value=value)


def make_assign_stmt(name_lexeme: str, value) -> ExpressionStmt:
    return ExpressionStmt(make_assign(name_lexeme, value))


def run_and_capture_prints(capsys, statements) -> list:
    ExecutorUnit().execute(statements)
    return capsys.readouterr().out.splitlines()


@pytest.mark.parametrize(
    "left, operator, right, expected",
    [
        (3.0, "+", 2.0, "5"),
        (3.0, "-", 2.0, "1"),
        (3.0, "*", 2.0, "6"),
        (3.0, "/", 2.0, "1.5"),
        (1.0, "<", 2.0, "참"),
        (3.0, ">", 5.0, "거짓"),
        (10.0, "==", 10.0, "참"),
        (10.0, "!=", 5.0, "참"),
        ("안녕, ", "+", "말랑!", "안녕, 말랑!"),
    ],
)
def test_이항_연산_결과를_출력한다(capsys, left, operator, right, expected):
    # 출력 <left> <operator> <right>;
    statement = PrintStmt(
        make_binary(left=Literal(left), operator_lexeme=operator, right=Literal(right))
    )

    assert run_and_capture_prints(capsys, [statement]) == [expected]


@pytest.mark.parametrize(
    "build_expression, expected",
    [
        # 1 + 2 * 3 -> 곱셈이 먼저 계산된다
        (
            lambda: make_binary(
                Literal(1.0), "+", make_binary(Literal(2.0), "*", Literal(3.0))
            ),
            "7",
        ),
        # (1 + 2) * 3 -> 괄호가 우선순위를 바꾼다
        (
            lambda: make_binary(
                Grouping(make_binary(Literal(1.0), "+", Literal(2.0))),
                "*",
                Literal(3.0),
            ),
            "9",
        ),
        # 10 - 4 - 3 -> 왼쪽부터 순서대로 계산된다
        (
            lambda: make_binary(
                make_binary(Literal(10.0), "-", Literal(4.0)), "-", Literal(3.0)
            ),
            "3",
        ),
        # 8 / 2 / 2 -> 왼쪽부터 순서대로 계산된다
        (
            lambda: make_binary(
                make_binary(Literal(8.0), "/", Literal(2.0)), "/", Literal(2.0)
            ),
            "2",
        ),
        # -3 + 2 -> 단항 마이너스가 리터럴에 적용된다
        (lambda: make_binary(make_unary(Literal(3.0)), "+", Literal(2.0)), "-1"),
    ],
)
def test_복합_표현식_트리를_우선순위와_결합_법칙에_따라_평가한다(
    capsys, build_expression, expected
):
    # Assembly Unit이 이런 Tree를 만들어준다고 가정
    statement = PrintStmt(build_expression())

    assert run_and_capture_prints(capsys, [statement]) == [expected]


@pytest.mark.parametrize(
    "value, expected",
    [
        (5.0, "5"),
        (3.14, "3.14"),
        (True, "참"),
        (False, "거짓"),
    ],
)
def test_리터럴_값을_형식에_맞게_출력한다(capsys, value, expected):
    # 출력 <value>;
    statement = PrintStmt(Literal(value))

    assert run_and_capture_prints(capsys, [statement]) == [expected]


def test_0으로_나누면_에러를_발생시킨다():
    statement = PrintStmt(
        make_binary(left=Literal(3.0), operator_lexeme="/", right=Literal(0.0))
    )

    executor = ExecutorUnit()

    with pytest.raises(ExecutorRuntimeError) as exc_info:
        executor.execute([statement])

    assert exc_info.value.message == "0으로 나눈 오류"
    assert exc_info.value.line == 1


def test_불리언_타입에_곱셈_연산을_하면_에러를_발생시킨다():
    # 출력 참 * 거짓;
    statement = PrintStmt(
        make_binary(left=Literal(True), operator_lexeme="*", right=Literal(False))
    )

    executor = ExecutorUnit()

    with pytest.raises(ExecutorRuntimeError) as exc_info:
        executor.execute([statement])

    assert exc_info.value.message == "피연산자는 반드시 숫자여야 합니다."


def test_덧셈에_숫자와_문자열이_혼용되면_에러를_발생시킨다():
    # 출력 1 + "HI";
    statement = PrintStmt(
        make_binary(left=Literal(1.0), operator_lexeme="+", right=Literal("HI"))
    )

    executor = ExecutorUnit()

    with pytest.raises(ExecutorRuntimeError) as exc_info:
        executor.execute([statement])

    assert (
        exc_info.value.message
        == "피연산자는 둘 다 숫자이거나 둘 다 문자열이어야 합니다."
    )


def test_뺄셈_피연산자가_숫자가_아니면_에러를_발생시킨다():
    statement = PrintStmt(
        make_binary(left=Literal(3.0), operator_lexeme="-", right=Literal("hello"))
    )

    executor = ExecutorUnit()

    with pytest.raises(ExecutorRuntimeError) as exc_info:
        executor.execute([statement])

    assert exc_info.value.message == "피연산자는 반드시 숫자여야 합니다."


def test_단항_마이너스_피연산자가_숫자가_아니면_에러를_발생시킨다():
    # 출력 -"말랑";
    statement = PrintStmt(make_unary(Literal("말랑")))

    executor = ExecutorUnit()

    with pytest.raises(ExecutorRuntimeError) as exc_info:
        executor.execute([statement])

    assert exc_info.value.message == "피연산자는 반드시 숫자여야 합니다."


def test_변수를_선언하고_재할당하면_최신_값을_사용한다(capsys):
    # 변수 a = 10; 변수 b = 20; 출력 a + b; a = a + 5; 출력 a;
    statements = [
        make_var_stmt("a", Literal(10.0)),
        make_var_stmt("b", Literal(20.0)),
        PrintStmt(
            make_binary(
                left=make_variable("a"), operator_lexeme="+", right=make_variable("b")
            )
        ),
        make_assign_stmt(
            "a",
            make_binary(
                left=make_variable("a"), operator_lexeme="+", right=Literal(5.0)
            ),
        ),
        PrintStmt(make_variable("a")),
    ]

    assert run_and_capture_prints(capsys, statements) == ["30", "15"]


def test_블록_스코프는_바깥_변수를_가리고_블록이_끝나면_복원된다(capsys):
    # 변수 x = "전역"; { 변수 x = "안쪽"; 출력 x; } 출력 x;
    statements = [
        make_var_stmt("x", Literal("전역")),
        BlockStmt([make_var_stmt("x", Literal("안쪽")), PrintStmt(make_variable("x"))]),
        PrintStmt(make_variable("x")),
    ]

    assert run_and_capture_prints(capsys, statements) == ["안쪽", "전역"]


def test_블록_내부의_대입은_바깥_스코프_변수를_수정한다(capsys):
    # 변수 count = 0; { count = count + 1; } 출력 count;
    statements = [
        make_var_stmt("count", Literal(0.0)),
        BlockStmt(
            [
                make_assign_stmt(
                    "count",
                    make_binary(
                        left=make_variable("count"),
                        operator_lexeme="+",
                        right=Literal(1.0),
                    ),
                )
            ]
        ),
        PrintStmt(make_variable("count")),
    ]

    assert run_and_capture_prints(capsys, statements) == ["1"]


def test_중첩된_블록에서_바깥_스코프_변수를_참조할_수_있다(capsys):
    # 변수 outer = "A"; { 변수 inner = "B"; { 출력 outer + inner; } }
    statements = [
        make_var_stmt("outer", Literal("A")),
        BlockStmt(
            [
                make_var_stmt("inner", Literal("B")),
                BlockStmt(
                    [
                        PrintStmt(
                            make_binary(
                                left=make_variable("outer"),
                                operator_lexeme="+",
                                right=make_variable("inner"),
                            )
                        )
                    ]
                ),
            ]
        ),
    ]

    assert run_and_capture_prints(capsys, statements) == ["AB"]


def test_만약_조건이_참이면_then_branch를_실행한다(capsys):
    var_declare = make_var_stmt("a", Literal(10.0))

    condition = make_binary(
        left=make_variable("a"), operator_lexeme=">", right=Literal(5.0)
    )
    then_branch = BlockStmt(
        [
            PrintStmt(
                make_binary(left=Literal(3.0), operator_lexeme="+", right=Literal(2.0))
            )
        ]
    )
    if_stmt = IfStmt(condition=condition, then_branch=then_branch, else_branch=None)

    assert run_and_capture_prints(capsys, [var_declare, if_stmt]) == ["5"]


def test_만약_조건이_거짓이고_아니면이_없으면_아무것도_출력하지_않는다(capsys):
    # 만약 (거짓) 출력 "no"; (아니면 없음 -> 아무것도 출력하지 않음)
    then_branch = PrintStmt(Literal("no"))
    if_stmt = IfStmt(
        condition=Literal(False), then_branch=then_branch, else_branch=None
    )

    assert run_and_capture_prints(capsys, [if_stmt]) == []


def test_만약_조건이_거짓이면_아니면_branch를_실행한다(capsys):
    # 만약 (거짓) 출력 "no"; 아니면 출력 "kfc";
    then_branch = PrintStmt(Literal("no"))
    else_branch = PrintStmt(Literal("kfc"))
    if_stmt = IfStmt(
        condition=Literal(False), then_branch=then_branch, else_branch=else_branch
    )

    assert run_and_capture_prints(capsys, [if_stmt]) == ["kfc"]


def test_아니면은_블록으로_감싼_가장_가까운_만약에_결합된다(capsys):
    # 만약 (참) { 만약 (거짓) 출력 "kfc"; 아니면 출력 "bbq"; }
    inner_if = IfStmt(
        condition=Literal(False),
        then_branch=PrintStmt(Literal("kfc")),
        else_branch=PrintStmt(Literal("bbq")),
    )
    outer_if = IfStmt(
        condition=Literal(True), then_branch=BlockStmt([inner_if]), else_branch=None
    )

    assert run_and_capture_prints(capsys, [outer_if]) == ["bbq"]


@pytest.mark.parametrize(
    "operator, left, right, expected_condition",
    [
        (">", 10.0, 5.0, True),
        (">", 3.0, 5.0, False),
        ("<", 3.0, 5.0, True),
        ("==", 10.0, 10.0, True),
        ("==", 10.0, 5.0, False),
    ],
)
def test_만약_조건을_비교_연산자로_평가한다(
    capsys, operator, left, right, expected_condition
):
    # 만약 (left <operator> right) 출력 "hit"; 아니면 출력 "miss";
    condition = make_binary(
        left=Literal(left), operator_lexeme=operator, right=Literal(right)
    )
    then_branch = PrintStmt(Literal("hit"))
    else_branch = PrintStmt(Literal("miss"))
    if_stmt = IfStmt(
        condition=condition, then_branch=then_branch, else_branch=else_branch
    )

    expected = "hit" if expected_condition else "miss"
    assert run_and_capture_prints(capsys, [if_stmt]) == [expected]


def test_정의되지_않은_변수를_참조하면_에러를_발생시킨다():
    # 출력 notDefined;
    statement = PrintStmt(make_variable("notDefined"))

    executor = ExecutorUnit()

    with pytest.raises(ExecutorRuntimeError) as exc_info:
        executor.execute([statement])

    assert exc_info.value.message == "정의되지 않은 변수 'notDefined'입니다."


def test_반복문이_조건을_만족하는_동안_반복해서_출력한다(capsys):
    # 반복 (변수 j = 0; j < 3; j = j + 1) { 출력 j; }
    for_stmt = ForStmt(
        initializer=make_var_stmt("j", Literal(0.0)),
        condition=make_binary(
            left=make_variable("j"), operator_lexeme="<", right=Literal(3.0)
        ),
        increment=make_assign(
            "j",
            make_binary(
                left=make_variable("j"), operator_lexeme="+", right=Literal(1.0)
            ),
        ),
        body=BlockStmt([PrintStmt(make_variable("j"))]),
    )

    assert run_and_capture_prints(capsys, [for_stmt]) == ["0", "1", "2"]


def test_반복문_조건이_처음부터_거짓이면_한번도_실행되지_않는다(capsys):
    # 반복 (변수 j = 0; j < 0; j = j + 1) { 출력 j; }
    for_stmt = ForStmt(
        initializer=make_var_stmt("j", Literal(0.0)),
        condition=make_binary(
            left=make_variable("j"), operator_lexeme="<", right=Literal(0.0)
        ),
        increment=make_assign(
            "j",
            make_binary(
                left=make_variable("j"), operator_lexeme="+", right=Literal(1.0)
            ),
        ),
        body=BlockStmt([PrintStmt(make_variable("j"))]),
    )

    assert run_and_capture_prints(capsys, [for_stmt]) == []
