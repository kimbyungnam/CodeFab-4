from codefab.assembler.call_expression_parser import CallExpressionParser
from codefab.assembler.statement_parser import StatementParser
from codefab.ast_nodes import Expr, FunctionStmt, ReturnStmt, Stmt
from codefab.tokens import Token, TokenType


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
        name = self._consume(TokenType.IDENTIFIER, "함수 이름이 필요합니다.")
        self._consume(TokenType.LEFT_PAREN, "함수 이름 뒤에는 '('가 필요합니다.")

        params: list[Token] = []
        if not self._check(TokenType.RIGHT_PAREN):
            params.append(
                self._consume(TokenType.IDENTIFIER, "파라미터 이름이 필요합니다.")
            )
            while self._match(TokenType.COMMA):
                params.append(
                    self._consume(TokenType.IDENTIFIER, "파라미터 이름이 필요합니다.")
                )

        self._consume(TokenType.RIGHT_PAREN, "파라미터 목록 뒤에는 ')'가 필요합니다.")
        self._consume(TokenType.LEFT_BRACE, "함수 본문은 '{'로 시작해야 합니다.")
        body = self._block()

        return FunctionStmt(name=name, params=params, body=body)

    def _return_statement(self) -> ReturnStmt:
        keyword = self._previous()

        value: Expr | None = None
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()

        self._consume(TokenType.SEMICOLON, "반환 값 뒤에는 ';'가 필요합니다.")
        return ReturnStmt(keyword=keyword, value=value)

    def _expression(self) -> Expr:
        parser = CallExpressionParser(self.tokens[self.current :])
        expression = parser.parse()
        self.current += parser.current
        return expression
