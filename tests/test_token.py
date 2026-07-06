import pytest

from codefab.token import Token, TokenType


def test_token_simple_exaple():
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
        "EOF",
    ],
)
def test_token_type_exists(name):
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
    ],
)
def test_token_stores_fixed_symbol_lexeme(token_type, lexeme):
    token = Token(type=token_type, lexeme=lexeme, literal=None, line=1)

    assert token.type == token_type
    assert token.lexeme == lexeme
    assert token.literal is None
