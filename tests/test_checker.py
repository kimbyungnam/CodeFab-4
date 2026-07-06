import pytest

from codefab.checker import Checker
from codefab.token import Token, TokenType


def test_정상_입력_확인():
    pass


def test_선언_전_사용_에러_검출(mocker):
    # arrange
    variable_a = mocker.Mock()
    variable_a.name = Token(type=TokenType.IDENTIFIER, lexeme="a", literal=None, line=1)
    variable_a.accept.side_effect = lambda visitor: visitor.visit_variable(variable_a)

    variable_b = mocker.Mock()
    variable_b.name = Token(type=TokenType.IDENTIFIER, lexeme="b", literal=None, line=1)
    variable_b.accept.side_effect = lambda visitor: visitor.visit_variable(variable_b)

    binary_expr = mocker.Mock(left=variable_a, right=variable_b)
    binary_expr.accept.side_effect = lambda visitor: visitor.visit_binary(binary_expr)

    exp_statement = mocker.Mock(expression=binary_expr)
    exp_statement.accept.side_effect = lambda visitor: visitor.visit_expression_stmt(
        exp_statement
    )

    ast = [exp_statement]
    sut = Checker()

    # act
    # assert
    with pytest.raises(ValueError, match="선언되지 않은 변수를 사용했습니다."):
        sut.resolve(ast)


def test_변수_중복_선언_에러_검출():
    pass


def test_지역_변수_초기화_시_자기_참조_에러_검출():
    pass
