import pytest

from codefab.ast_nodes import Binary, ExpressionStmt, Variable
from codefab.checker import Checker
from codefab.tokens import Token, TokenType


def test_정상_입력_확인():
    pass


def test_선언_전_사용_에러_검출():
    # arrange
    exp_statement = ExpressionStmt(
        Binary(
            left=Variable(
                Token(type=TokenType.IDENTIFIER, lexeme="a", literal=None, line=1)
            ),
            operator=Token(type=TokenType.PLUS, lexeme="+", literal=None, line=1),
            right=Variable(
                Token(type=TokenType.IDENTIFIER, lexeme="b", literal=None, line=1)
            ),
        )
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
