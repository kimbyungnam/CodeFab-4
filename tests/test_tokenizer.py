import pytest

from codefab.error import ParseError
from codefab.tokenizer import Tokenizer
from codefab.tokens import Token, TokenType


def test_빈_소스는_EOF_토큰만_반환한다():
    tokens = Tokenizer("").scan_tokens()

    assert tokens == [Token(type=TokenType.EOF, lexeme="", literal=None, line=1)]


def test_왼쪽_괄호_토큰을_인식한다():
    tokens = Tokenizer("(").scan_tokens()

    assert tokens == [
        Token(type=TokenType.LEFT_PAREN, lexeme="(", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_오른쪽_괄호_토큰을_인식한다():
    tokens = Tokenizer(")").scan_tokens()

    assert tokens == [
        Token(type=TokenType.RIGHT_PAREN, lexeme=")", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_플러스_토큰을_인식한다():
    tokens = Tokenizer("+").scan_tokens()

    assert tokens == [
        Token(type=TokenType.PLUS, lexeme="+", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_세미콜론_토큰을_인식한다():
    tokens = Tokenizer(";").scan_tokens()

    assert tokens == [
        Token(type=TokenType.SEMICOLON, lexeme=";", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


@pytest.mark.parametrize(
    "source,expected_literal",
    [
        ("3.14", 3.14),
        ("5.0", 5.0),
    ],
)
def test_소수_숫자_토큰을_인식한다(source, expected_literal):
    tokens = Tokenizer(source).scan_tokens()

    assert tokens == [
        Token(type=TokenType.NUMBER, lexeme=source, literal=expected_literal, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_점_뒤에_숫자가_없으면_소수로_인식하지_않는다():
    tokens = Tokenizer("3.").scan_tokens()

    assert tokens[0] == Token(type=TokenType.NUMBER, lexeme="3", literal=3.0, line=1)


def test_대입식_예제_토큰화():
    tokens = Tokenizer("age = 37").scan_tokens()

    assert tokens == [
        Token(type=TokenType.IDENTIFIER, lexeme="age", literal=None, line=1),
        Token(type=TokenType.EQUAL, lexeme="=", literal=None, line=1),
        Token(type=TokenType.NUMBER, lexeme="37", literal=37.0, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_조건식_예제_토큰화():
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


def test_산술식_예제_토큰화():
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
        ("아니면", TokenType.ELSE),
        ("변수", TokenType.VAR),
        ("반복", TokenType.FOR),
        ("출력", TokenType.PRINT),
        ("참", TokenType.TRUE),
        ("거짓", TokenType.FALSE),
        ("그리고", TokenType.AND),
        ("또는", TokenType.OR),
        ("함수", TokenType.FUNC),
        ("반환", TokenType.RETURN),
        ("클래스", TokenType.CLASS),
        ("나", TokenType.THIS),
        ("생성자", TokenType.INIT),
        ("부모", TokenType.SUPER),
        ("배열", TokenType.ARRAY),
        ("가져오기", TokenType.IMPORT),
        ("별칭", TokenType.ALIAS),
        ("instanceof", TokenType.INSTANCEOF),
    ],
)
def test_한글_키워드_토큰을_인식한다(source, expected_type):
    tokens = Tokenizer(source).scan_tokens()

    assert tokens == [
        Token(type=expected_type, lexeme=source, literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


@pytest.mark.parametrize(
    "source,expected_type",
    [
        ("[", TokenType.LEFT_BRACKET),
        ("]", TokenType.RIGHT_BRACKET),
        (",", TokenType.COMMA),
        (".", TokenType.DOT),
        (":", TokenType.COLON),
    ],
)
def test_함수_클래스_배열_구두점_토큰을_인식한다(source, expected_type):
    tokens = Tokenizer(source).scan_tokens()

    assert tokens == [
        Token(type=expected_type, lexeme=source, literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_점_표기로_필드_접근을_토큰화한다():
    tokens = Tokenizer("r.name").scan_tokens()

    assert tokens == [
        Token(type=TokenType.IDENTIFIER, lexeme="r", literal=None, line=1),
        Token(type=TokenType.DOT, lexeme=".", literal=None, line=1),
        Token(type=TokenType.IDENTIFIER, lexeme="name", literal=None, line=1),
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
def test_두글자_연산자_토큰을_인식한다(source, expected_type):
    tokens = Tokenizer(source).scan_tokens()

    assert tokens == [
        Token(type=expected_type, lexeme=source, literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_느낌표_토큰을_인식한다():
    tokens = Tokenizer("!").scan_tokens()

    assert tokens == [
        Token(type=TokenType.BANG, lexeme="!", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_문자열_토큰을_인식한다():
    tokens = Tokenizer('"hello"').scan_tokens()

    assert tokens == [
        Token(type=TokenType.STRING, lexeme='"hello"', literal="hello", line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_한글_문자열_연결을_토큰화한다():
    tokens = Tokenizer('출력 "안녕, " + "말랑!";').scan_tokens()

    assert tokens == [
        Token(type=TokenType.PRINT, lexeme="출력", literal=None, line=1),
        Token(type=TokenType.STRING, lexeme='"안녕, "', literal="안녕, ", line=1),
        Token(type=TokenType.PLUS, lexeme="+", literal=None, line=1),
        Token(type=TokenType.STRING, lexeme='"말랑!"', literal="말랑!", line=1),
        Token(type=TokenType.SEMICOLON, lexeme=";", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_닫히지_않은_문자열은_ParseError를_발생시킨다():
    with pytest.raises(ParseError):
        Tokenizer('"unterminated').scan_tokens()


def test_한글_조건식_예제_토큰화():
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
