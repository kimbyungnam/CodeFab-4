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


def test_executor_prints_binary_plus_result(mocker):
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
def test_executor_prints_binary_arithmetic_result(mocker, operator, expected):
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


def test_executor_evaluates_nested_binary_tree(mocker):
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


def test_executor_raises_error_when_dividing_by_zero(mocker):
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


def test_executor_raises_error_when_operand_is_not_number(mocker):
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
