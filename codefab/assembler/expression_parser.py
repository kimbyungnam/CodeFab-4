from typing import Callable

from codefab.array_nodes import ArrayLiteral, IndexGet, IndexSet
from codefab.ast_nodes import (
    Assign,
    Binary,
    Expr,
    Grouping,
    Literal,
    Logical,
    Unary,
    Variable,
)
from codefab.error import ParseError
from codefab.tokens import Token, TokenType

ARRAY_KEYWORD_LEXEME = "Array"


class ExpressionParser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Expr:
        return self._assignment()

    def _assignment(self) -> Expr:
        expression = self._logic_or()
        if self._match(TokenType.EQUAL):
            equals = self._previous()
            value = self._assignment()
            if isinstance(expression, Variable):
                return Assign(expression.name, value)
            if isinstance(expression, IndexGet):
                return IndexSet(
                    expression.target, expression.index, value, expression.line
                )
            raise ParseError("잘못된 대입 대상입니다.", equals.line)
        return expression

    def _logic_or(self) -> Expr:
        return self._left_assoc(Logical, self._logic_and, TokenType.OR)

    def _logic_and(self) -> Expr:
        return self._left_assoc(Logical, self._equality, TokenType.AND)

    def _equality(self) -> Expr:
        return self._left_assoc(
            Binary, self._comparison, TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL
        )

    def _comparison(self) -> Expr:
        return self._left_assoc(
            Binary,
            self._term,
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        )

    def _term(self) -> Expr:
        return self._left_assoc(Binary, self._factor, TokenType.PLUS, TokenType.MINUS)

    def _factor(self) -> Expr:
        return self._left_assoc(Binary, self._unary, TokenType.STAR, TokenType.SLASH)

    def _left_assoc(
        self,
        node_class: type[Binary] | type[Logical],
        operand_rule: Callable[[], Expr],
        *operator_types: TokenType,
    ) -> Expr:
        expression = operand_rule()
        while self._match(*operator_types):
            operator = self._previous()
            right = operand_rule()
            expression = node_class(expression, operator, right)
        return expression

    def _unary(self) -> Expr:
        if self._match(TokenType.MINUS, TokenType.BANG):
            operator = self._previous()
            right = self._unary()
            return Unary(operator, right)
        return self._index_access()

    def _index_access(self) -> Expr:
        expression = self._primary()
        while self._match(TokenType.LEFT_BRACKET):
            bracket_line = self._previous().line
            index = self.parse()
            self._consume(TokenType.RIGHT_BRACKET, "인덱스 뒤에는 ']'가 필요합니다.")
            expression = IndexGet(expression, index, bracket_line)
        return expression

    def _primary(self) -> Expr:
        if self._match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self._previous().literal)
        if self._match(TokenType.TRUE):
            return Literal(True)
        if self._match(TokenType.FALSE):
            return Literal(False)
        if self._is_array_literal_start():
            return self._array_literal()
        if self._match(TokenType.IDENTIFIER):
            return Variable(self._previous())
        if self._match(TokenType.LEFT_PAREN):
            expression = self.parse()
            self._consume(TokenType.RIGHT_PAREN, "표현식 뒤에는 ')'가 필요합니다.")
            return Grouping(expression)
        raise NotImplementedError("아직 처리하지 않는 표현식 종류입니다.")

    def _is_array_literal_start(self) -> bool:
        return (
            self._check(TokenType.IDENTIFIER)
            and self._peek().lexeme == ARRAY_KEYWORD_LEXEME
            and self._check_next(TokenType.LEFT_PAREN)
        )

    def _array_literal(self) -> Expr:
        array_token = self._advance()  # "Array" 소비
        self._advance()  # "(" 소비
        size = self.parse()
        self._consume(TokenType.RIGHT_PAREN, "표현식 뒤에는 ')'가 필요합니다.")
        return ArrayLiteral(size, array_token.line)

    # ---------------- helpers ----------------

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        raise ParseError(message, self._peek().line)

    def _match(self, *types: TokenType) -> bool:
        for token_type in types:
            if self._check(token_type):
                self._advance()
                return True
        return False

    def _check(self, token_type: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == token_type

    def _check_next(self, token_type: TokenType) -> bool:
        next_index = self.current + 1
        if next_index >= len(self.tokens):
            return False
        return self.tokens[next_index].type == token_type

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]
