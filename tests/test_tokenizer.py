import pytest

from codefab.assembler.errors import ParseError
from codefab.tokenizer import Tokenizer
from codefab.tokens import Token, TokenType


def test_empty_source_returns_only_eof_token():
    tokens = Tokenizer("").scan_tokens()

    assert tokens == [Token(type=TokenType.EOF, lexeme="", literal=None, line=1)]


def test_left_paren_token():
    tokens = Tokenizer("(").scan_tokens()

    assert tokens == [
        Token(type=TokenType.LEFT_PAREN, lexeme="(", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_right_paren_token():
    tokens = Tokenizer(")").scan_tokens()

    assert tokens == [
        Token(type=TokenType.RIGHT_PAREN, lexeme=")", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_plus_token():
    tokens = Tokenizer("+").scan_tokens()

    assert tokens == [
        Token(type=TokenType.PLUS, lexeme="+", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_semicolon_token():
    tokens = Tokenizer(";").scan_tokens()

    assert tokens == [
        Token(type=TokenType.SEMICOLON, lexeme=";", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_example_one_page_24():
    tokens = Tokenizer("age = 37").scan_tokens()

    assert tokens == [
        Token(type=TokenType.IDENTIFIER, lexeme="age", literal=None, line=1),
        Token(type=TokenType.EQUAL, lexeme="=", literal=None, line=1),
        Token(type=TokenType.NUMBER, lexeme="37", literal=37.0, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_example_two_page_25():
    tokens = Tokenizer("if ( x > 10 )").scan_tokens()

    assert tokens == [
        Token(type=TokenType.IF, lexeme="if", literal=None, line=1),
        Token(type=TokenType.LEFT_PAREN, lexeme="(", literal=None, line=1),
        Token(type=TokenType.IDENTIFIER, lexeme="x", literal=None, line=1),
        Token(type=TokenType.GREATER, lexeme=">", literal=None, line=1),
        Token(type=TokenType.NUMBER, lexeme="10", literal=10.0, line=1),
        Token(type=TokenType.RIGHT_PAREN, lexeme=")", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_example_three_page_26():
    tokens = Tokenizer("a + b * 3").scan_tokens()

    assert tokens == [
        Token(type=TokenType.IDENTIFIER, lexeme="a", literal=None, line=1),
        Token(type=TokenType.PLUS, lexeme="+", literal=None, line=1),
        Token(type=TokenType.IDENTIFIER, lexeme="b", literal=None, line=1),
        Token(type=TokenType.STAR, lexeme="*", literal=None, line=1),
        Token(type=TokenType.NUMBER, lexeme="3", literal=3.0, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


@pytest.mark.parametrize(
    "source,expected_type",
    [
        ("만약", TokenType.IF),
        ("변수", TokenType.VAR),
        ("출력", TokenType.PRINT),
    ],
)
def test_korean_keyword_tokens(source, expected_type):
    tokens = Tokenizer(source).scan_tokens()

    assert tokens == [
        Token(type=expected_type, lexeme=source, literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


@pytest.mark.parametrize(
    "source,expected_type",
    [
        ("==", TokenType.EQUAL_EQUAL),
        (">=", TokenType.GREATER_EQUAL),
        ("<=", TokenType.LESS_EQUAL),
        ("!=", TokenType.BANG_EQUAL),
    ],
)
def test_double_char_operator_tokens(source, expected_type):
    tokens = Tokenizer(source).scan_tokens()

    assert tokens == [
        Token(type=expected_type, lexeme=source, literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_bang_token():
    tokens = Tokenizer("!").scan_tokens()

    assert tokens == [
        Token(type=TokenType.BANG, lexeme="!", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_string_token():
    tokens = Tokenizer('"hello"').scan_tokens()

    assert tokens == [
        Token(type=TokenType.STRING, lexeme='"hello"', literal="hello", line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_korean_string_concat_token():
    tokens = Tokenizer('출력 "안녕, " + "말랑!";').scan_tokens()

    assert tokens == [
        Token(type=TokenType.PRINT, lexeme="출력", literal=None, line=1),
        Token(type=TokenType.STRING, lexeme='"안녕, "', literal="안녕, ", line=1),
        Token(type=TokenType.PLUS, lexeme="+", literal=None, line=1),
        Token(type=TokenType.STRING, lexeme='"말랑!"', literal="말랑!", line=1),
        Token(type=TokenType.SEMICOLON, lexeme=";", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_unterminated_string_raises_parse_error():
    with pytest.raises(ParseError):
        Tokenizer('"unterminated').scan_tokens()


def test_example_two_page_25_korean():
    tokens = Tokenizer("만약 ( x > 10 )").scan_tokens()

    assert tokens == [
        Token(type=TokenType.IF, lexeme="만약", literal=None, line=1),
        Token(type=TokenType.LEFT_PAREN, lexeme="(", literal=None, line=1),
        Token(type=TokenType.IDENTIFIER, lexeme="x", literal=None, line=1),
        Token(type=TokenType.GREATER, lexeme=">", literal=None, line=1),
        Token(type=TokenType.NUMBER, lexeme="10", literal=10.0, line=1),
        Token(type=TokenType.RIGHT_PAREN, lexeme=")", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]
