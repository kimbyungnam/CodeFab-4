import pytest

from codefab.executor_unit import ExecutorRuntimeError, ExecutorUnit


# 실제 AST 클래스가 아님.
# Mock spec 용 계약 클래스일 뿐입니다.
class PrintStmt:
    expression = None


class Literal:
    value = None


class Binary:
    left = None
    operator = None
    right = None


class Variable:
    name = None


class VarDeclareStmt:
    name = None
    initializer = None


class BlockStmt:
    statements = None


class IfStmt:
    condition = None
    then_branch = None
    else_branch = None


class Token:
    lexeme = None
    line = None


def mock_token(mocker, lexeme: str, line: int = 1):
    token = mocker.Mock(spec=Token)
    token.lexeme = lexeme
    token.line = line
    return token


def mock_literal(mocker, value):
    node = mocker.Mock(spec=Literal)
    node.value = value
    return node


def mock_binary(mocker, left, operator_lexeme: str, right):
    node = mocker.Mock(spec=Binary)
    node.left = left
    node.operator = mock_token(mocker, operator_lexeme)
    node.right = right
    return node


def mock_print_stmt(mocker, expression):
    node = mocker.Mock(spec=PrintStmt)
    node.expression = expression
    return node


def mock_variable(mocker, name_lexeme: str):
    node = mocker.Mock(spec=Variable)
    node.name = mock_token(mocker, name_lexeme)
    return node


def mock_var_declare_stmt(mocker, name_lexeme: str, initializer):
    node = mocker.Mock(spec=VarDeclareStmt)
    node.name = mock_token(mocker, name_lexeme)
    node.initializer = initializer
    return node


def mock_block_stmt(mocker, statements):
    node = mocker.Mock(spec=BlockStmt)
    node.statements = statements
    return node


def mock_if_stmt(mocker, condition, then_branch, else_branch=None):
    node = mocker.Mock(spec=IfStmt)
    node.condition = condition
    node.then_branch = then_branch
    node.else_branch = else_branch
    return node


def test_이항_덧셈_결과를_출력한다(mocker):
    # 출력 3 + 2;
    statement = mock_print_stmt(
        mocker,
        mock_binary(
            mocker,
            left=mock_literal(mocker, 3.0),
            operator_lexeme="+",
            right=mock_literal(mocker, 2.0),
        ),
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
    statement = mock_print_stmt(
        mocker,
        mock_binary(
            mocker,
            left=mock_literal(mocker, 3.0),
            operator_lexeme=operator,
            right=mock_literal(mocker, 2.0),
        ),
    )

    print_mock = mocker.patch("builtins.print")
    executor = ExecutorUnit()

    executor.execute([statement])

    print_mock.assert_called_once_with(expected)


def test_중첩된_이항_트리를_연산자_우선순위대로_평가한다(mocker):
    # 출력 1 + 2 * 3;
    # Assembly Unit이 이런 Tree를 만들어준다고 가정
    expression = mock_binary(
        mocker,
        left=mock_literal(mocker, 1.0),
        operator_lexeme="+",
        right=mock_binary(
            mocker,
            left=mock_literal(mocker, 2.0),
            operator_lexeme="*",
            right=mock_literal(mocker, 3.0),
        ),
    )

    statement = mock_print_stmt(mocker, expression)

    print_mock = mocker.patch("builtins.print")
    executor = ExecutorUnit()

    executor.execute([statement])

    print_mock.assert_called_once_with("7")


def test_0으로_나누면_에러를_발생시킨다(mocker):
    statement = mock_print_stmt(
        mocker,
        mock_binary(
            mocker,
            left=mock_literal(mocker, 3.0),
            operator_lexeme="/",
            right=mock_literal(mocker, 0.0),
        ),
    )

    executor = ExecutorUnit()

    with pytest.raises(ExecutorRuntimeError) as exc_info:
        executor.execute([statement])

    assert exc_info.value.message == "0으로 나눈 오류"
    assert exc_info.value.line == 1


def test_피연산자가_숫자가_아니면_에러를_발생시킨다(mocker):
    statement = mock_print_stmt(
        mocker,
        mock_binary(
            mocker,
            left=mock_literal(mocker, 3.0),
            operator_lexeme="+",
            right=mock_literal(mocker, "hello"),
        ),
    )

    executor = ExecutorUnit()

    with pytest.raises(ExecutorRuntimeError) as exc_info:
        executor.execute([statement])

    assert exc_info.value.message == "피연산자는 반드시 숫자여야 합니다."


def test_만약_조건이_참이면_then_branch를_실행한다(mocker):
    var_declare = mock_var_declare_stmt(mocker, "a", mock_literal(mocker, 10.0))

    condition = mock_binary(
        mocker,
        left=mock_variable(mocker, "a"),
        operator_lexeme=">",
        right=mock_literal(mocker, 5.0),
    )
    then_branch = mock_block_stmt(
        mocker,
        [
            mock_print_stmt(
                mocker,
                mock_binary(
                    mocker,
                    left=mock_literal(mocker, 3.0),
                    operator_lexeme="+",
                    right=mock_literal(mocker, 2.0),
                ),
            )
        ],
    )
    if_stmt = mock_if_stmt(mocker, condition, then_branch)

    print_mock = mocker.patch("builtins.print")
    executor = ExecutorUnit()

    executor.execute([var_declare, if_stmt])

    print_mock.assert_called_once_with("5")


def test_만약_조건이_거짓이고_아니면이_없으면_아무것도_출력하지_않는다(mocker):
    # 만약 (거짓) 출력 "no"; (아니면 없음 -> 아무것도 출력하지 않음)
    then_branch = mock_print_stmt(mocker, mock_literal(mocker, "no"))
    if_stmt = mock_if_stmt(mocker, mock_literal(mocker, False), then_branch)

    print_mock = mocker.patch("builtins.print")
    executor = ExecutorUnit()

    executor.execute([if_stmt])

    print_mock.assert_not_called()


def test_만약_조건이_거짓이면_아니면_branch를_실행한다(mocker):
    # 만약 (거짓) 출력 "no"; 아니면 출력 "kfc";
    then_branch = mock_print_stmt(mocker, mock_literal(mocker, "no"))
    else_branch = mock_print_stmt(mocker, mock_literal(mocker, "kfc"))
    if_stmt = mock_if_stmt(
        mocker, mock_literal(mocker, False), then_branch, else_branch
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
    condition = mock_binary(
        mocker,
        left=mock_literal(mocker, left),
        operator_lexeme=operator,
        right=mock_literal(mocker, right),
    )
    then_branch = mock_print_stmt(mocker, mock_literal(mocker, "hit"))
    else_branch = mock_print_stmt(mocker, mock_literal(mocker, "miss"))
    if_stmt = mock_if_stmt(mocker, condition, then_branch, else_branch)

    print_mock = mocker.patch("builtins.print")
    executor = ExecutorUnit()

    executor.execute([if_stmt])

    print_mock.assert_called_once_with("hit" if expected_condition else "miss")


def test_정의되지_않은_변수를_참조하면_에러를_발생시킨다(mocker):
    # 출력 notDefined;
    statement = mock_print_stmt(mocker, mock_variable(mocker, "notDefined"))

    executor = ExecutorUnit()

    with pytest.raises(ExecutorRuntimeError) as exc_info:
        executor.execute([statement])

    assert exc_info.value.message == "정의되지 않은 변수 'notDefined'입니다."
