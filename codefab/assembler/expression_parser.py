from typing import Callable

from codefab.ast_nodes import (
    Assign,
    Binary,
    Call,
    Expr,
    Get,
    Grouping,
    InstanceOf,
    Literal,
    Logical,
    Set,
    Super,
    This,
    Unary,
    Variable,
)
from codefab.error import ParseError
from codefab.tokens import Token, TokenType


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
            if isinstance(expression, Get):
                return Set(expression.object, expression.name, value)
            raise ParseError("잘못된 대입 대상입니다.", equals.line)
        return expression

    def _logic_or(self) -> Expr:
        return self._left_assoc(Logical, self._logic_and, TokenType.OR)

    def _logic_and(self) -> Expr:
        return self._left_assoc(Logical, self._equality, TokenType.AND)

    def _equality(self) -> Expr:
        return self._left_assoc(
            Binary, self._instance_of, TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL
        )

    def _instance_of(self) -> Expr:
        expression = self._comparison()
        while self._match(TokenType.INSTANCEOF):
            class_name = self._consume(
                TokenType.IDENTIFIER, "'instanceof' 뒤에는 클래스 이름이 필요합니다."
            )
            expression = InstanceOf(expression, Variable(class_name))
        return expression

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
        return self._call()

    def _call(self) -> Expr:
        expression = self._primary()
        while True:
            if self._match(TokenType.LEFT_PAREN):
                expression = self._finish_call(expression)
            elif self._match(TokenType.DOT):
                name = self._consume(
                    TokenType.IDENTIFIER, "'.' 뒤에는 속성 이름이 필요합니다."
                )
                expression = Get(expression, name)
            else:
                break
        return expression

    def _finish_call(self, callee: Expr) -> Expr:
        arguments = []
        if not self._check(TokenType.RIGHT_PAREN):
            arguments.append(self._assignment())
            while self._match(TokenType.COMMA):
                arguments.append(self._assignment())
        paren = self._consume(
            TokenType.RIGHT_PAREN, "인자 목록 뒤에는 ')'가 필요합니다."
        )
        return Call(callee, paren, arguments)

    def _primary(self) -> Expr:
        if self._match(TokenType.NUMBER, TokenType.STRING):
            return Literal(self._previous().literal)
        if self._match(TokenType.TRUE):
            return Literal(True)
        if self._match(TokenType.FALSE):
            return Literal(False)
        if self._match(TokenType.THIS):
            return This(self._previous())
        if self._match(TokenType.SUPER):
            keyword = self._previous()
            self._consume(TokenType.DOT, "'Super' 뒤에는 '.'이 필요합니다.")
            method = self._consume(
                TokenType.IDENTIFIER, "'Super.' 뒤에는 메서드 이름이 필요합니다."
            )
            return Super(keyword, method)
        if self._match(TokenType.IDENTIFIER):
            return Variable(self._previous())
        if self._match(TokenType.LEFT_PAREN):
            expression = self.parse()
            self._consume(TokenType.RIGHT_PAREN, "표현식 뒤에는 ')'가 필요합니다.")
            return Grouping(expression)
        raise NotImplementedError("아직 처리하지 않는 표현식 종류입니다.")

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
