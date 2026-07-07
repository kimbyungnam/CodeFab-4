import pytest

from codefab.assembler.expr import Binary, Literal, Variable
from codefab.ast_nodes import BlockStmt, IfStmt, PrintStmt, VarStmt
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
}


def make_operator_token(lexeme: str, line: int = 1) -> Token:
    return Token(
        type=OPERATOR_TOKEN_TYPES[lexeme], lexeme=lexeme, literal=None, line=line
    )


def make_identifier_token(lexeme: str, line: int = 1) -> Token:
    return Token(type=TokenType.IDENTIFIER, lexeme=lexeme, literal=None, line=line)


def make_binary(left, operator_lexeme: str, right) -> Binary:
    return Binary(left=left, operator=make_operator_token(operator_lexeme), right=right)


def make_variable(name_lexeme: str) -> Variable:
    return Variable(name=make_identifier_token(name_lexeme))


def make_var_stmt(name_lexeme: str, initializer) -> VarStmt:
    return VarStmt(name=make_identifier_token(name_lexeme), initializer=initializer)


def test_이항_덧셈_결과를_출력한다(mocker):
    # 출력 3 + 2;
    statement = PrintStmt(
        make_binary(left=Literal(3.0), operator_lexeme="+", right=Literal(2.0))
    )

    print_mock = mocker.patch("builtins.print")
    executor = ExecutorUnit()

    executor.execute([statement])

    print_mock.assert_called_once_with("5")


@pytest.mark.parametrize(
    "operator, expected",
    [
        ("+", "5"),
        ("-", "1"),
        ("*", "6"),
        ("/", "1.5"),
    ],
)
def test_이항_산술_연산_결과를_출력한다(mocker, operator, expected):
    statement = PrintStmt(
        make_binary(left=Literal(3.0), operator_lexeme=operator, right=Literal(2.0))
    )

    print_mock = mocker.patch("builtins.print")
    executor = ExecutorUnit()

    executor.execute([statement])

    print_mock.assert_called_once_with(expected)


def test_중첩된_이항_트리를_연산자_우선순위대로_평가한다(mocker):
    # 출력 1 + 2 * 3;
    # Assembly Unit이 이런 Tree를 만들어준다고 가정
    expression = make_binary(
        left=Literal(1.0),
        operator_lexeme="+",
        right=make_binary(left=Literal(2.0), operator_lexeme="*", right=Literal(3.0)),
    )

    statement = PrintStmt(expression)

    print_mock = mocker.patch("builtins.print")
    executor = ExecutorUnit()

    executor.execute([statement])

    print_mock.assert_called_once_with("7")


def test_0으로_나누면_에러를_발생시킨다(mocker):
    statement = PrintStmt(
        make_binary(left=Literal(3.0), operator_lexeme="/", right=Literal(0.0))
    )

    executor = ExecutorUnit()

    with pytest.raises(ExecutorRuntimeError) as exc_info:
        executor.execute([statement])

    assert exc_info.value.message == "0으로 나눈 오류"
    assert exc_info.value.line == 1


def test_피연산자가_숫자가_아니면_에러를_발생시킨다(mocker):
    statement = PrintStmt(
        make_binary(left=Literal(3.0), operator_lexeme="+", right=Literal("hello"))
    )

    executor = ExecutorUnit()

    with pytest.raises(ExecutorRuntimeError) as exc_info:
        executor.execute([statement])

    assert exc_info.value.message == "피연산자는 반드시 숫자여야 합니다."


def test_만약_조건이_참이면_then_branch를_실행한다(mocker):
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

    print_mock = mocker.patch("builtins.print")
    executor = ExecutorUnit()

    executor.execute([var_declare, if_stmt])

    print_mock.assert_called_once_with("5")


def test_만약_조건이_거짓이고_아니면이_없으면_아무것도_출력하지_않는다(mocker):
    # 만약 (거짓) 출력 "no"; (아니면 없음 -> 아무것도 출력하지 않음)
    then_branch = PrintStmt(Literal("no"))
    if_stmt = IfStmt(
        condition=Literal(False), then_branch=then_branch, else_branch=None
    )

    print_mock = mocker.patch("builtins.print")
    executor = ExecutorUnit()

    executor.execute([if_stmt])

    print_mock.assert_not_called()


def test_만약_조건이_거짓이면_아니면_branch를_실행한다(mocker):
    # 만약 (거짓) 출력 "no"; 아니면 출력 "kfc";
    then_branch = PrintStmt(Literal("no"))
    else_branch = PrintStmt(Literal("kfc"))
    if_stmt = IfStmt(
        condition=Literal(False), then_branch=then_branch, else_branch=else_branch
    )

    print_mock = mocker.patch("builtins.print")
    executor = ExecutorUnit()

    executor.execute([if_stmt])

    print_mock.assert_called_once_with("kfc")


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
    mocker, operator, left, right, expected_condition
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

    print_mock = mocker.patch("builtins.print")
    executor = ExecutorUnit()

    executor.execute([if_stmt])

    print_mock.assert_called_once_with("hit" if expected_condition else "miss")


def test_정의되지_않은_변수를_참조하면_에러를_발생시킨다(mocker):
    # 출력 notDefined;
    statement = PrintStmt(make_variable("notDefined"))

    executor = ExecutorUnit()

    with pytest.raises(ExecutorRuntimeError) as exc_info:
        executor.execute([statement])

    assert exc_info.value.message == "정의되지 않은 변수 'notDefined'입니다."
