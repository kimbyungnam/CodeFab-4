from codefab.ast_nodes import Binary, ExpressionStmt, Stmt, Variable, VarStmt


class Checker:
    def __init__(self):
        self.declared: set[str] = set()

    def resolve(self, statements: list[Stmt]):
        for stmt in statements:
            stmt.accept(self)

    def visit_expression_stmt(self, stmt: ExpressionStmt):
        stmt.expression.accept(self)

    def visit_var_stmt(self, stmt: VarStmt):
        if stmt.name.lexeme in self.declared:
            raise ValueError("이미 선언된 변수입니다.")
        self.declared.add(stmt.name.lexeme)

    def visit_variable(self, expr: Variable):
        if expr.name.lexeme not in self.declared:
            raise ValueError("선언되지 않은 변수를 사용했습니다.")

    def visit_binary(self, expr: Binary):
        expr.left.accept(self)
        expr.right.accept(self)
