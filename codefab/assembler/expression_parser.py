from assembler.errors import ParseError
from assembler.expr import Grouping, Literal, Variable
from assembler.tokens import TokenType


class ExpressionParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def parse(self):
        return self._primary()

    def _primary(self):
        if self._match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self._previous().literal)
        if self._match(TokenType.TRUE):
            return Literal(True)
        if self._match(TokenType.FALSE):
            return Literal(False)
        if self._match(TokenType.IDENTIFIER):
            return Variable(self._previous())
        if self._match(TokenType.LEFT_PAREN):
            expression = self.parse()
            self._consume(TokenType.RIGHT_PAREN, "표현식 뒤에는 ')'가 필요합니다.")
            return Grouping(expression)
        raise NotImplementedError("아직 처리하지 않는 표현식 종류입니다.")

    def _consume(self, token_type, message):
        if self._check(token_type):
            return self._advance()
        raise ParseError(message, self._peek().line)

    def _match(self, *types):
        for token_type in types:
            if self._check(token_type):
                self._advance()
                return True
        return False

    def _check(self, token_type):
        if self._is_at_end():
            return False
        return self._peek().type == token_type

    def _advance(self):
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self):
        return self._peek().type == TokenType.EOF

    def _peek(self):
        return self.tokens[self.current]

    def _previous(self):
        return self.tokens[self.current - 1]
