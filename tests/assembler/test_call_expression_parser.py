import pytest

from codefab.assembler.call_expression_parser import CallExpressionParser
from codefab.ast import Binary, Call, Literal, Variable
from codefab.common.tokens import Token, TokenType
from codefab.errors import ParseError


def _tok(token_type, lexeme, literal=None, line=1):
    return Token(token_type, lexeme, literal=literal, line=line)


def _eof(line=1):
    return _tok(TokenType.EOF, "", line=line)


def test_괄호가_뒤따르지_않는_식별자는_기존과_같이_Variable로_파싱된다():
    tokens = [_tok(TokenType.IDENTIFIER, "a"), _eof()]

    expression = CallExpressionParser(tokens).parse()

    assert isinstance(expression, Variable)
    assert expression.name.lexeme == "a"


def test_기존_이항_연산_파싱_동작도_그대로_유지된다():
    # a + b
    tokens = [
        _tok(TokenType.IDENTIFIER, "a"),
        _tok(TokenType.PLUS, "+"),
        _tok(TokenType.IDENTIFIER, "b"),
        _eof(),
    ]

    expression = CallExpressionParser(tokens).parse()

    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == "+"


def test_인자가_없는_호출은_Call로_파싱된다():
    # add()
    tokens = [
        _tok(TokenType.IDENTIFIER, "add"),
        _tok(TokenType.LEFT_PAREN, "("),
        _tok(TokenType.RIGHT_PAREN, ")"),
        _eof(),
    ]

    expression = CallExpressionParser(tokens).parse()

    assert isinstance(expression, Call)
    assert expression.arguments == []
    assert expression.callee.name.lexeme == "add"


def test_여러_인자를_가진_호출은_콤마로_구분되어_파싱된다():
    # add(1, 2, 3)
    tokens = [
        _tok(TokenType.IDENTIFIER, "add"),
        _tok(TokenType.LEFT_PAREN, "("),
        _tok(TokenType.NUMBER, "1", literal=1.0),
        _tok(TokenType.COMMA, ","),
        _tok(TokenType.NUMBER, "2", literal=2.0),
        _tok(TokenType.COMMA, ","),
        _tok(TokenType.NUMBER, "3", literal=3.0),
        _tok(TokenType.RIGHT_PAREN, ")"),
        _eof(),
    ]

    expression = CallExpressionParser(tokens).parse()

    assert expression.arguments == [Literal(1.0), Literal(2.0), Literal(3.0)]


def test_인자_표현식은_이항연산도_허용한다():
    # add(1 + 2, 3)
    tokens = [
        _tok(TokenType.IDENTIFIER, "add"),
        _tok(TokenType.LEFT_PAREN, "("),
        _tok(TokenType.NUMBER, "1", literal=1.0),
        _tok(TokenType.PLUS, "+"),
        _tok(TokenType.NUMBER, "2", literal=2.0),
        _tok(TokenType.COMMA, ","),
        _tok(TokenType.NUMBER, "3", literal=3.0),
        _tok(TokenType.RIGHT_PAREN, ")"),
        _eof(),
    ]

    expression = CallExpressionParser(tokens).parse()

    assert isinstance(expression.arguments[0], Binary)
    assert expression.arguments[1] == Literal(3.0)


def test_괄호로_묶인_호출대상도_호출할_수_있다():
    # (add)(1)
    tokens = [
        _tok(TokenType.LEFT_PAREN, "("),
        _tok(TokenType.IDENTIFIER, "add"),
        _tok(TokenType.RIGHT_PAREN, ")"),
        _tok(TokenType.LEFT_PAREN, "("),
        _tok(TokenType.NUMBER, "1", literal=1.0),
        _tok(TokenType.RIGHT_PAREN, ")"),
        _eof(),
    ]

    expression = CallExpressionParser(tokens).parse()

    assert isinstance(expression, Call)
    assert expression.arguments == [Literal(1.0)]


def test_닫는_괄호가_없으면_에러():
    # add(1
    tokens = [
        _tok(TokenType.IDENTIFIER, "add"),
        _tok(TokenType.LEFT_PAREN, "("),
        _tok(TokenType.NUMBER, "1", literal=1.0),
        _eof(),
    ]

    with pytest.raises(ParseError, match="인자 목록 뒤에는 '\\)'가 필요합니다."):
        CallExpressionParser(tokens).parse()
