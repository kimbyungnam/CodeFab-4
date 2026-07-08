from codefab.error import ParseError
from codefab.tokens import Token, TokenType

SINGLE_CHAR_TOKENS: dict[str, TokenType] = {
    "(": TokenType.LEFT_PAREN,
    ")": TokenType.RIGHT_PAREN,
    "{": TokenType.LEFT_BRACE,
    "}": TokenType.RIGHT_BRACE,
    "[": TokenType.LEFT_BRACKET,
    "]": TokenType.RIGHT_BRACKET,
    ";": TokenType.SEMICOLON,
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.STAR,
    "/": TokenType.SLASH,
    "=": TokenType.EQUAL,
    ">": TokenType.GREATER,
    "<": TokenType.LESS,
    "!": TokenType.BANG,
    ",": TokenType.COMMA,
    ".": TokenType.DOT,
}

DOUBLE_CHAR_TOKENS: dict[str, TokenType] = {
    "=": TokenType.EQUAL_EQUAL,
    ">": TokenType.GREATER_EQUAL,
    "<": TokenType.LESS_EQUAL,
    "!": TokenType.BANG_EQUAL,
}

KEYWORDS: dict[str, TokenType] = {
    "if": TokenType.IF,
    "만약": TokenType.IF,
    "else": TokenType.ELSE,
    "아니면": TokenType.ELSE,
    "var": TokenType.VAR,
    "변수": TokenType.VAR,
    "for": TokenType.FOR,
    "반복": TokenType.FOR,
    "print": TokenType.PRINT,
    "출력": TokenType.PRINT,
    "true": TokenType.TRUE,
    "참": TokenType.TRUE,
    "false": TokenType.FALSE,
    "거짓": TokenType.FALSE,
    "and": TokenType.AND,
    "그리고": TokenType.AND,
    "or": TokenType.OR,
    "또는": TokenType.OR,
    "func": TokenType.FUN,
    "함수": TokenType.FUN,
    "return": TokenType.RETURN,
    "반환": TokenType.RETURN,
    "import": TokenType.IMPORT,
    "가져오기": TokenType.IMPORT,
    "alias": TokenType.ALIAS,
    "별칭": TokenType.ALIAS,
}


class Tokenizer:
    def __init__(self, source: str):
        self.source = source
        self.tokens: list[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1

    def scan_tokens(self) -> list[Token]:
        while not self._is_at_end():
            self.start = self.current
            current_token = self.source[self.current]
            self.current += 1
            if current_token in (" ", "\t"):
                continue
            if current_token == "\n":
                self.line += 1
                continue
            if current_token in DOUBLE_CHAR_TOKENS and self._match_next("="):
                self._add(DOUBLE_CHAR_TOKENS[current_token])
                continue
            if current_token == '"':
                self._string()
                continue
            if current_token in SINGLE_CHAR_TOKENS:
                self._add(SINGLE_CHAR_TOKENS[current_token])
                continue
            if current_token.isdigit():
                self._number()
                continue
            if current_token.isalpha() or current_token == "_":
                self._identifier()
                continue
        self.tokens.append(
            Token(type=TokenType.EOF, lexeme="", literal=None, line=self.line)
        )
        return self.tokens

    def _add(self, token_type: TokenType, literal: object = None):
        lexeme = self.source[self.start : self.current]
        self.tokens.append(
            Token(type=token_type, lexeme=lexeme, literal=literal, line=self.line)
        )

    def _number(self):
        while not self._is_at_end() and self.source[self.current].isdigit():
            self.current += 1

        if self._peek_is_decimal_point():
            self.current += 1  # 소수점 '.' 소비
            while not self._is_at_end() and self.source[self.current].isdigit():
                self.current += 1

        lexeme = self.source[self.start : self.current]
        self._add(TokenType.NUMBER, literal=float(lexeme))

    def _peek_is_decimal_point(self) -> bool:
        return (
            not self._is_at_end()
            and self.source[self.current] == "."
            and self.current + 1 < len(self.source)
            and self.source[self.current + 1].isdigit()
        )

    def _string(self) -> None:
        while not self._is_at_end() and self.source[self.current] != '"':
            if self.source[self.current] == "\n":
                self.line += 1
            self.current += 1

        if self._is_at_end():
            raise ParseError("문자열이 닫히지 않았습니다.", self.line)

        self.current += 1  # 닫는 '"' 소비
        value = self.source[self.start + 1 : self.current - 1]
        self._add(TokenType.STRING, literal=value)

    def _identifier(self):
        while not self._is_at_end() and (
            self.source[self.current].isalnum() or self.source[self.current] == "_"
        ):
            self.current += 1
        lexeme = self.source[self.start : self.current]
        self._add(KEYWORDS.get(lexeme, TokenType.IDENTIFIER))

    def _match_next(self, expected: str) -> bool:
        if self._is_at_end() or self.source[self.current] != expected:
            return False
        self.current += 1
        return True

    def _is_at_end(self) -> bool:
        return self.current >= len(self.source)
