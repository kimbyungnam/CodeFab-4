from assembler.errors import ParseError
from assembler.expr import Binary, Grouping, Literal, Unary, Variable
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
        return self._equality()

    def _equality(self):
        return self._left_assoc_binary(
            self._comparison, TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL
        )

    def _comparison(self):
        return self._left_assoc_binary(
            self._term,
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        )

    def _term(self):
        return self._left_assoc_binary(self._factor, TokenType.PLUS, TokenType.MINUS)

    def _factor(self):
        return self._left_assoc_binary(self._unary, TokenType.STAR, TokenType.SLASH)

    def _left_assoc_binary(self, operand_rule, *operator_types):
        """left (op right)* 형태의 좌결합 이항연산 문법 규칙 공통 처리.

        operand_rule: 한 단계 더 높은 우선순위의 파싱 메서드 (예: _term -> _factor)
        """
        expression = operand_rule()
        while self._match(*operator_types):
            operator = self._previous()
            right = operand_rule()
            expression = Binary(expression, operator, right)
        return expression

    def _unary(self):
        if self._match(TokenType.MINUS, TokenType.BANG):
            operator = self._previous()
            right = self._unary()
            return Unary(operator, right)
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

    # ---------------- helpers ----------------
    # (다음 단계에서 _logic_and/_logic_or, _assignment 가 추가될 자리)

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
