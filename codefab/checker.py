from codefab.ast_nodes import Binary, BlockStmt, ExpressionStmt, Stmt, Variable, VarStmt


class Checker:
    def __init__(self):
        self.declared: set[str] = set()
        self.initializing: str | None = None

    def resolve(self, statements: list[Stmt]):
        for stmt in statements:
            stmt.accept(self)

    def visit_expression_stmt(self, stmt: ExpressionStmt):
        stmt.expression.accept(self)

    def visit_block_stmt(self, stmt: BlockStmt):
        for statement in stmt.statements:
            statement.accept(self)

    def visit_var_stmt(self, stmt: VarStmt):
        if stmt.name.lexeme in self.declared:
            raise ValueError("이미 선언된 변수입니다.")
        if stmt.initializer is not None:
            self.initializing = stmt.name.lexeme
            stmt.initializer.accept(self)
            self.initializing = None
        self.declared.add(stmt.name.lexeme)

    def visit_variable(self, expr: Variable):
        if expr.name.lexeme == self.initializing:
            raise ValueError("지역 변수 자기 참조 에러입니다.")
        if expr.name.lexeme not in self.declared:
            raise ValueError("선언되지 않은 변수를 사용했습니다.")

    def visit_binary(self, expr: Binary):
        expr.left.accept(self)
        expr.right.accept(self)
