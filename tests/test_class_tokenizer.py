import pytest

from codefab.tokenizer import Tokenizer
from codefab.tokens import Token, TokenType


@pytest.mark.parametrize(
    "source, expected_type",
    [
        ("클래스", TokenType.CLASS),
        ("나", TokenType.THIS),
        ("부모", TokenType.SUPER),
        ("타입확인", TokenType.INSTANCEOF),
    ],
)
def test_클래스_관련_키워드를_인식한다(source, expected_type):
    tokens = Tokenizer(source).scan_tokens()

    assert tokens == [
        Token(type=expected_type, lexeme=source, literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_점_토큰을_인식한다():
    tokens = Tokenizer(".").scan_tokens()

    assert tokens == [
        Token(type=TokenType.DOT, lexeme=".", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_쉼표_토큰을_인식한다():
    tokens = Tokenizer(",").scan_tokens()

    assert tokens == [
        Token(type=TokenType.COMMA, lexeme=",", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_콜론_토큰을_인식한다():
    tokens = Tokenizer(":").scan_tokens()

    assert tokens == [
        Token(type=TokenType.COLON, lexeme=":", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_필드_접근에_사용되는_점은_숫자_리터럴의_소수점과_구분된다():
    # r.speed 처럼 식별자 뒤의 '.'은 DOT 토큰이지 소수점이 아니다
    tokens = Tokenizer("r.speed").scan_tokens()

    assert [t.type for t in tokens] == [
        TokenType.IDENTIFIER,
        TokenType.DOT,
        TokenType.IDENTIFIER,
        TokenType.EOF,
    ]


def test_상속_문법에_사용되는_콜론을_인식한다():
    # 클래스 SpeedRobot : Robot { }
    tokens = Tokenizer("클래스 SpeedRobot : Robot { }").scan_tokens()

    assert [t.type for t in tokens] == [
        TokenType.CLASS,
        TokenType.IDENTIFIER,
        TokenType.COLON,
        TokenType.IDENTIFIER,
        TokenType.LEFT_BRACE,
        TokenType.RIGHT_BRACE,
        TokenType.EOF,
    ]
