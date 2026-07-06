"""Token 계약(contract) 정의.

주의: 이 파일은 Tokenizer 담당 팀원의 tokens.py 와 이름/필드가 반드시 같아야 합니다.
지금은 Expression 파싱에 필요한 종류만 우선 정의했고, 나중에 팀원의 Tokenizer 결과물과
합칠 때 이 파일을 팀에서 합의한 공용 tokens.py 로 교체(또는 통합)하면 됩니다.
"""

from enum import Enum, auto


class TokenType(Enum):
    # 그룹핑
    LEFT_PAREN = auto()
    RIGHT_PAREN = auto()

    # 산술 연산
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()

    # 대입/비교/논리 연산자
    EQUAL = auto()
    EQUAL_EQUAL = auto()
    BANG = auto()
    BANG_EQUAL = auto()
    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()
    AND = auto()
    OR = auto()

    # 리터럴/식별자
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()
    TRUE = auto()
    FALSE = auto()

    EOF = auto()


class Token:
    def __init__(self, type, origin, line=1, literal=None):
        self.type = type
        self.origin = origin
        self.line = line
        self.literal = literal

    def __repr__(self):
        return f"Token({self.type.name}, {self.origin!r}, literal={self.literal!r})"
