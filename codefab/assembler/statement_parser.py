from codefab.assembler.expression_parser import ExpressionParser
from codefab.ast_nodes import (
    BlockStmt,
    ClassStmt,
    Expr,
    ExpressionStmt,
    ForStmt,
    IfStmt,
    ImportStmt,
    MethodDecl,
    PrintStmt,
    Stmt,
    Variable,
    VarStmt,
)
from codefab.error import ParseError
from codefab.tokens import Token, TokenType


class StatementParser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> list[Stmt]:
        statements = []
        while not self.is_at_end():
            statements.append(self.parse_statement())
        return statements

    def is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def parse_statement(self) -> Stmt:
        if self._match(TokenType.PRINT):
            return self._print_statement()
        if self._match(TokenType.LEFT_BRACE):
            return BlockStmt(self._block())
        if self._match(TokenType.VAR):
            return self._var_declaration()
        if self._match(TokenType.IF):
            return self._if_statement()
        if self._match(TokenType.FOR):
            return self._for_statement()
        if self._match(TokenType.CLASS):
            return self._class_declaration()
        if self._match(TokenType.IMPORT):
            return self._import_statement()
        return self._expression_statement()

    def _class_declaration(self) -> ClassStmt:
        name = self._consume(TokenType.IDENTIFIER, "클래스 이름이 필요합니다.")

        superclass = None
        if self._match(TokenType.COLON):
            super_name = self._consume(
                TokenType.IDENTIFIER, "상속할 클래스 이름이 필요합니다."
            )
            superclass = Variable(super_name)

        self._consume(TokenType.LEFT_BRACE, "클래스 본문은 '{'로 시작해야 합니다.")
        methods = []
        while not self._check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            methods.append(self._method_declaration())
        self._consume(TokenType.RIGHT_BRACE, "클래스 본문은 '}'로 닫아야 합니다.")

        return ClassStmt(name, superclass, methods)

    def _method_declaration(self) -> MethodDecl:
        name = self._consume(TokenType.IDENTIFIER, "메서드 이름이 필요합니다.")
        self._consume(TokenType.LEFT_PAREN, "메서드 이름 뒤에는 '('가 필요합니다.")

        params = []
        if not self._check(TokenType.RIGHT_PAREN):
            params.append(
                self._consume(TokenType.IDENTIFIER, "매개변수 이름이 필요합니다.")
            )
            while self._match(TokenType.COMMA):
                params.append(
                    self._consume(TokenType.IDENTIFIER, "매개변수 이름이 필요합니다.")
                )
        self._consume(TokenType.RIGHT_PAREN, "매개변수 목록 뒤에는 ')'가 필요합니다.")

        self._consume(TokenType.LEFT_BRACE, "메서드 본문은 '{'로 시작해야 합니다.")
        body = self._block()

        return MethodDecl(name, params, body)

    def _print_statement(self) -> PrintStmt:
        expression = self._expression()
        self._consume(TokenType.SEMICOLON, "값 뒤에는 ';'가 필요합니다.")
        return PrintStmt(expression)

    def _block(self) -> list[Stmt]:
        statements = []
        while not self._check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.parse_statement())
        self._consume(TokenType.RIGHT_BRACE, "블록은 '}'로 닫아야 합니다.")
        return statements

    def _for_statement(self) -> ForStmt:
        self._consume(TokenType.LEFT_PAREN, "'반복' 뒤에는 '('가 필요합니다.")

        if self._match(TokenType.SEMICOLON):
            initializer = None
        elif self._match(TokenType.VAR):
            initializer = self._var_declaration()
        else:
            initializer = self._expression_statement()

        condition = None
        if not self._check(TokenType.SEMICOLON):
            condition = self._expression()
        self._consume(TokenType.SEMICOLON, "조건식 뒤에는 ';'가 필요합니다.")

        increment = None
        if not self._check(TokenType.RIGHT_PAREN):
            increment = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "증감식 뒤에는 ')'가 필요합니다.")

        body = self.parse_statement()

        return ForStmt(initializer, condition, increment, body)

    def _var_declaration(self) -> VarStmt:
        name = self._consume(TokenType.IDENTIFIER, "변수 이름이 필요합니다.")

        initializer = None
        if self._match(TokenType.EQUAL):
            initializer = self._expression()

        self._consume(TokenType.SEMICOLON, "변수 선언 뒤에는 ';'가 필요합니다.")
        return VarStmt(name, initializer)

    def _if_statement(self) -> IfStmt:
        self._consume(TokenType.LEFT_PAREN, "'만약' 뒤에는 '('가 필요합니다.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "조건식 뒤에는 ')'가 필요합니다.")

        then_branch = self.parse_statement()
        else_branch = None
        if self._match(TokenType.ELSE):
            else_branch = self.parse_statement()

        return IfStmt(condition, then_branch, else_branch)

    def _import_statement(self) -> ImportStmt:
        path = self._consume(
            TokenType.STRING, "가져올 파일 경로는 문자열이어야 합니다."
        )
        self._consume(TokenType.ALIAS, "'별칭' 키워드가 필요합니다.")
        alias = self._consume(TokenType.IDENTIFIER, "별칭 이름이 필요합니다.")
        self._consume(TokenType.SEMICOLON, "가져오기 문 뒤에는 ';'가 필요합니다.")
        return ImportStmt(path, alias)

    def _expression_statement(self) -> ExpressionStmt:
        expression = self._expression()
        self._consume(TokenType.SEMICOLON, "값 뒤에는 ';'가 필요합니다.")
        return ExpressionStmt(expression)

    def _expression(self) -> Expr:
        parser = ExpressionParser(self.tokens[self.current :])
        expression = parser.parse()
        self.current += parser.current
        return expression

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
        if self.is_at_end():
            return False
        return self._peek().type == token_type

    def _advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self._previous()

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]
