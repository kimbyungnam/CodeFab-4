from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenType(Enum):
    # 구분자 / 그룹핑
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()
    LEFT_BRACE = auto()
    RIGHT_BRACE = auto()
    SEMICOLON = auto()
    COMMA = auto()
    DOT = auto()
    COLON = auto()

    # 연산자
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    BANG = auto()
    BANG_EQUAL = auto()
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()

    # 리터럴 / 식별자
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    # 키워드
    VAR = auto()
    IF = auto()
    ELSE = auto()
    FOR = auto()
    TRUE = auto()
    FALSE = auto()
    AND = auto()
    OR = auto()
    PRINT = auto()
    CLASS = auto()
    THIS = auto()
    SUPER = auto()
    INSTANCEOF = auto()

    EOF = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str  # 원본 문자열
    literal: Any  # 실제 값 (NUMBER→float, STRING→str, 그 외 None)
    line: int  # 오류 리포팅용 라인 번호
