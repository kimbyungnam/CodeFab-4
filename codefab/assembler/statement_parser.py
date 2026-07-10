from codefab.assembler.expression_parser import ExpressionParser
from codefab.ast import (
    BlockStmt,
    ClassStmt,
    Expr,
    ExpressionStmt,
    ForStmt,
    IfStmt,
    ImportStmt,
    MethodDecl,
    PrintStmt,
    ReturnStmt,
    Stmt,
    Variable,
    VarStmt,
)
from codefab.common.tokens import Token, TokenType
from codefab.errors import (
    MissingAliasKeywordError,
    MissingAliasNameError,
    MissingClassNameError,
    MissingClosingBraceError,
    MissingImportPathError,
    MissingLeftBraceForClassBodyError,
    MissingLeftBraceForMethodBodyError,
    MissingLeftParenAfterForError,
    MissingLeftParenAfterIfError,
    MissingLeftParenAfterMethodNameError,
    MissingMethodNameError,
    MissingParameterNameError,
    MissingRightBraceForClassBodyError,
    MissingRightParenAfterIfConditionError,
    MissingRightParenAfterIncrementError,
    MissingRightParenAfterParameterListError,
    MissingSemicolonAfterForConditionError,
    MissingSemicolonAfterImportError,
    MissingSemicolonAfterReturnError,
    MissingSemicolonAfterValueError,
    MissingSemicolonAfterVarDeclarationError,
    MissingSuperclassNameError,
    MissingVariableNameError,
    ParseError,
    UnexpectedEndOfInputError,
)


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
        if self._match(TokenType.RETURN):
            return self._return_statement()
        return self._expression_statement()

    def _return_statement(self) -> ReturnStmt:
        keyword = self._previous()

        value: Expr | None = None
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()

        self._consume(TokenType.SEMICOLON, MissingSemicolonAfterReturnError)
        return ReturnStmt(keyword=keyword, value=value)

    def _class_declaration(self) -> ClassStmt:
        name = self._consume(TokenType.IDENTIFIER, MissingClassNameError)

        superclass = None
        if self._match(TokenType.COLON):
            super_name = self._consume(TokenType.IDENTIFIER, MissingSuperclassNameError)
            superclass = Variable(super_name)

        self._consume(TokenType.LEFT_BRACE, MissingLeftBraceForClassBodyError)
        methods = []
        while not self._check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            methods.append(self._method_declaration())
        self._consume(TokenType.RIGHT_BRACE, MissingRightBraceForClassBodyError)

        return ClassStmt(name, superclass, methods)

    def _method_declaration(self) -> MethodDecl:
        name = self._consume(TokenType.IDENTIFIER, MissingMethodNameError)
        self._consume(TokenType.LEFT_PAREN, MissingLeftParenAfterMethodNameError)

        params = []
        if not self._check(TokenType.RIGHT_PAREN):
            params.append(
                self._consume(TokenType.IDENTIFIER, MissingParameterNameError)
            )
            while self._match(TokenType.COMMA):
                params.append(
                    self._consume(TokenType.IDENTIFIER, MissingParameterNameError)
                )
        self._consume(TokenType.RIGHT_PAREN, MissingRightParenAfterParameterListError)

        self._consume(TokenType.LEFT_BRACE, MissingLeftBraceForMethodBodyError)
        body = self._block()

        return MethodDecl(name, params, body)

    def _print_statement(self) -> PrintStmt:
        expression = self._expression()
        self._consume(TokenType.SEMICOLON, MissingSemicolonAfterValueError)
        return PrintStmt(expression)

    def _block(self) -> list[Stmt]:
        statements = []
        while not self._check(TokenType.RIGHT_BRACE) and not self.is_at_end():
            statements.append(self.parse_statement())
        self._consume(TokenType.RIGHT_BRACE, MissingClosingBraceError)
        return statements

    def _for_statement(self) -> ForStmt:
        self._consume(TokenType.LEFT_PAREN, MissingLeftParenAfterForError)

        if self._match(TokenType.SEMICOLON):
            initializer = None
        elif self._match(TokenType.VAR):
            initializer = self._var_declaration()
        else:
            initializer = self._expression_statement()

        condition = None
        if not self._check(TokenType.SEMICOLON):
            condition = self._expression()
        self._consume(TokenType.SEMICOLON, MissingSemicolonAfterForConditionError)

        increment = None
        if not self._check(TokenType.RIGHT_PAREN):
            increment = self._expression()
        self._consume(TokenType.RIGHT_PAREN, MissingRightParenAfterIncrementError)

        body = self.parse_statement()

        return ForStmt(initializer, condition, increment, body)

    def _var_declaration(self) -> VarStmt:
        name = self._consume(TokenType.IDENTIFIER, MissingVariableNameError)

        initializer = None
        if self._match(TokenType.EQUAL):
            initializer = self._expression()

        self._consume(TokenType.SEMICOLON, MissingSemicolonAfterVarDeclarationError)
        return VarStmt(name, initializer)

    def _if_statement(self) -> IfStmt:
        self._consume(TokenType.LEFT_PAREN, MissingLeftParenAfterIfError)
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, MissingRightParenAfterIfConditionError)

        then_branch = self.parse_statement()
        else_branch = None
        if self._match(TokenType.ELSE):
            else_branch = self.parse_statement()

        return IfStmt(condition, then_branch, else_branch)

    def _import_statement(self) -> ImportStmt:
        path = self._consume(TokenType.STRING, MissingImportPathError)
        self._consume(TokenType.ALIAS, MissingAliasKeywordError)
        alias = self._consume(TokenType.IDENTIFIER, MissingAliasNameError)
        self._consume(TokenType.SEMICOLON, MissingSemicolonAfterImportError)
        return ImportStmt(path, alias)

    def _expression_statement(self) -> ExpressionStmt:
        expression = self._expression()
        self._consume(TokenType.SEMICOLON, MissingSemicolonAfterValueError)
        return ExpressionStmt(expression)

    def _expression(self) -> Expr:
        parser = ExpressionParser(self.tokens[self.current :])
        expression = parser.parse()
        self.current += parser.current
        return expression

    # ---------------- helpers ----------------

    def _consume(self, token_type: TokenType, error_type: type[ParseError]) -> Token:
        if self._check(token_type):
            return self._advance()
        if self.is_at_end():
            raise UnexpectedEndOfInputError(
                error_type(self._peek().line).message, self._peek().line
            )
        raise error_type(self._peek().line)

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
