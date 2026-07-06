from assembler.expr import Literal
from assembler.tokens import TokenType


class ExpressionParser:
    """Token List 를 Expr 트리로 조립하는 파서.

    [1단계] 지금은 숫자 리터럴 하나만 처리한다.
    다음 단계에서 문자열/불리언/변수/괄호/단항/이항/논리/대입을 순서대로 추가한다.
    """

    def __init__(self, tokens):
        self.tokens = tokens
        self.current = 0

    def parse(self):
        return self._primary()

    def _primary(self):
        if self._match(TokenType.NUMBER):
            return Literal(self._previous().literal)
        raise NotImplementedError(
            "아직 NUMBER 리터럴 이외의 표현식은 처리하지 않습니다."
        )

    # ---------------- helpers ----------------
    # (다음 단계에서 _unary/_term/_factor 등 우선순위 체인이 추가될 자리)

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
