import pytest

from codefab.checker import Checker
from codefab.tokens import Token, TokenType


def make_token(lexeme, line=1):
    return Token(type=TokenType.IDENTIFIER, lexeme=lexeme, literal=None, line=line)


@pytest.fixture
def sut():
    return Checker()


@pytest.fixture
def make_variable(mocker):
    def _make(lexeme, line=1):
        variable = mocker.Mock()
        variable.name = make_token(lexeme, line)
        variable.accept.side_effect = lambda visitor: visitor.visit_variable(variable)
        return variable

    return _make


@pytest.fixture
def make_var_stmt(mocker):
    def _make(lexeme, initializer=None, line=1):
        var_stmt = mocker.Mock(initializer=initializer)
        var_stmt.name = make_token(lexeme, line)
        var_stmt.accept.side_effect = lambda visitor: visitor.visit_var_stmt(var_stmt)
        return var_stmt

    return _make


@pytest.fixture
def make_exp_stmt(mocker):
    def _make(expression):
        exp_stmt = mocker.Mock(expression=expression)
        exp_stmt.accept.side_effect = lambda visitor: visitor.visit_expression_stmt(
            exp_stmt
        )
        return exp_stmt

    return _make


@pytest.fixture
def make_binary(mocker):
    def _make(left, right):
        binary = mocker.Mock(left=left, right=right)
        binary.accept.side_effect = lambda visitor: visitor.visit_binary(binary)
        return binary

    return _make


@pytest.fixture
def make_block_stmt(mocker):
    def _make(statements):
        block_stmt = mocker.Mock(statements=statements)
        block_stmt.accept.side_effect = lambda visitor: visitor.visit_block_stmt(
            block_stmt
        )
        return block_stmt

    return _make


def test_정상_입력_확인(sut, make_var_stmt, make_variable, make_exp_stmt):
    # arrange
    var_stmt_a = make_var_stmt("a", line=1)
    variable_a = make_variable("a", line=2)
    exp_statement = make_exp_stmt(variable_a)

    ast = [var_stmt_a, exp_statement]

    # act
    sut.resolve(ast)

    # assert
    assert sut.declared == {"a"}


def test_선언_전_사용_에러_검출(sut, make_variable, make_binary, make_exp_stmt):
    # arrange
    variable_a = make_variable("a")
    variable_b = make_variable("b")
    binary_expr = make_binary(variable_a, variable_b)
    exp_statement = make_exp_stmt(binary_expr)

    ast = [exp_statement]

    # act
    # assert
    with pytest.raises(ValueError, match="선언되지 않은 변수를 사용했습니다."):
        sut.resolve(ast)


def test_변수_중복_선언_에러_검출(sut, make_var_stmt):
    # arrange
    var_stmt_a1 = make_var_stmt("a", line=1)
    var_stmt_a2 = make_var_stmt("a", line=2)

    ast = [var_stmt_a1, var_stmt_a2]

    # act
    # assert
    with pytest.raises(ValueError, match="이미 선언된 변수입니다."):
        sut.resolve(ast)


def test_지역_변수_초기화_시_자기_참조_에러_검출(
    sut, make_variable, make_var_stmt, make_block_stmt
):
    # arrange
    variable_a = make_variable("a")
    var_stmt_a = make_var_stmt("a", initializer=variable_a)
    block_stmt = make_block_stmt([var_stmt_a])

    ast = [block_stmt]

    # act
    # assert
    with pytest.raises(ValueError, match="지역 변수 자기 참조 에러입니다."):
        sut.resolve(ast)
