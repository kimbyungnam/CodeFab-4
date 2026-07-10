from codefab.assembler.call_expression_parser import CallExpressionParser
from codefab.assembler.statement_parser import StatementParser
from codefab.ast import Expr, FunctionStmt, ReturnStmt, Stmt
from codefab.common.tokens import Token, TokenType
from codefab.errors import (
    MissingFunctionNameError,
    MissingFunctionParameterNameError,
    MissingLeftBraceForFunctionBodyError,
    MissingLeftParenAfterFunctionNameError,
    MissingRightParenAfterFunctionParameterListError,
    MissingSemicolonAfterReturnError,
)


class FunctionStatementParser(StatementParser):
    """StatementParser에 함수 선언(`함수 add(a, b) { ... }`)과 반환문(`반환 ...;`)을 추가한다.

    StatementParser의 기존 메서드(parse_statement, _block, _if_statement,
    _for_statement 등)는 전부 `self.xxx()` 형태로 서로를 호출하기 때문에, 이
    서브클래스에서 parse_statement와 _expression만 오버라이드해도 다형성 덕분에
    모든 문장 파싱 경로가 함수 선언/호출을 함께 인식한다. 즉 기존 파일은 한 줄도
    바꾸지 않는다.
    """

    def parse_statement(self) -> Stmt:
        if self._match(TokenType.FUN):
            return self._function_declaration()
        if self._match(TokenType.RETURN):
            return self._return_statement()
        return super().parse_statement()

    def _function_declaration(self) -> FunctionStmt:
        name = self._consume(TokenType.IDENTIFIER, MissingFunctionNameError)
        self._consume(TokenType.LEFT_PAREN, MissingLeftParenAfterFunctionNameError)

        params: list[Token] = []
        if not self._check(TokenType.RIGHT_PAREN):
            params.append(
                self._consume(TokenType.IDENTIFIER, MissingFunctionParameterNameError)
            )
            while self._match(TokenType.COMMA):
                params.append(
                    self._consume(
                        TokenType.IDENTIFIER, MissingFunctionParameterNameError
                    )
                )

        self._consume(
            TokenType.RIGHT_PAREN, MissingRightParenAfterFunctionParameterListError
        )
        self._consume(TokenType.LEFT_BRACE, MissingLeftBraceForFunctionBodyError)
        body = self._block()

        return FunctionStmt(name=name, params=params, body=body)

    def _return_statement(self) -> ReturnStmt:
        keyword = self._previous()

        value: Expr | None = None
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()

        self._consume(TokenType.SEMICOLON, MissingSemicolonAfterReturnError)
        return ReturnStmt(keyword=keyword, value=value)

    def _expression(self) -> Expr:
        parser = CallExpressionParser(self.tokens[self.current :])
        expression = parser.parse()
        self.current += parser.current
        return expression
