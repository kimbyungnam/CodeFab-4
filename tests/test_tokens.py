import pytest

from codefab.common.tokens import Token, TokenType


def test_토큰_필드가_정확히_저장된다():
    token = Token(type=TokenType.NUMBER, lexeme="3.14", literal=3.14, line=1)

    assert token.type == TokenType.NUMBER
    assert token.lexeme == "3.14"
    assert token.literal == 3.14
    assert token.line == 1


@pytest.mark.parametrize(
    "name",
    [
        "LEFT_PAREN",
        "RIGHT_PAREN",
        "LEFT_BRACE",
        "RIGHT_BRACE",
        "SEMICOLON",
        "PLUS",
        "MINUS",
        "STAR",
        "SLASH",
        "EQUAL",
        "GREATER",
        "LESS",
        "IDENTIFIER",
        "STRING",
        "NUMBER",
        "VAR",
        "IF",
        "ELSE",
        "FOR",
        "TRUE",
        "FALSE",
        "AND",
        "OR",
        "PRINT",
        "IMPORT",
        "ALIAS",
        "DOT",
        "EOF",
    ],
)
def test_토큰타입이_존재한다(name):
    assert hasattr(TokenType, name)


@pytest.mark.parametrize(
    "token_type,lexeme",
    [
        (TokenType.LEFT_PAREN, "("),
        (TokenType.RIGHT_PAREN, ")"),
        (TokenType.LEFT_BRACE, "{"),
        (TokenType.RIGHT_BRACE, "}"),
        (TokenType.SEMICOLON, ";"),
        (TokenType.PLUS, "+"),
        (TokenType.MINUS, "-"),
        (TokenType.STAR, "*"),
        (TokenType.SLASH, "/"),
        (TokenType.EQUAL, "="),
        (TokenType.GREATER, ">"),
        (TokenType.LESS, "<"),
        (TokenType.DOT, "."),
    ],
)
def test_토큰이_고정_기호_렉심을_저장한다(token_type, lexeme):
    token = Token(type=token_type, lexeme=lexeme, literal=None, line=1)

    assert token.type == token_type
    assert token.lexeme == lexeme
    assert token.literal is None


@pytest.mark.parametrize(
    "token_type,lexeme",
    [
        (TokenType.PRINT, "출력"),
        (TokenType.VAR, "변수"),
        (TokenType.IF, "만약"),
        (TokenType.IMPORT, "가져오기"),
        (TokenType.ALIAS, "별칭"),
    ],
)
def test_토큰이_한글_키워드_렉심을_저장한다(token_type, lexeme):
    token = Token(type=token_type, lexeme=lexeme, literal=None, line=1)

    assert token.type == token_type
    assert token.lexeme == lexeme
    assert token.literal is None
