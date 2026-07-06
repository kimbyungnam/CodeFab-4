from codefab.ast_nodes import Binary, ExpressionStmt, Stmt, Variable


class Checker:
    def __init__(self):
        self.declared: set[str] = set()

    def resolve(self, statements: list[Stmt]):
        for stmt in statements:
            stmt.accept(self)

    def visit_expression_stmt(self, stmt: ExpressionStmt):
        stmt.expression.accept(self)

    def visit_variable(self, expr: Variable):
        if expr.name.lexeme not in self.declared:
            raise ValueError("선언되지 않은 변수를 사용했습니다.")

    def visit_binary(self, expr: Binary):
        expr.left.accept(self)
        expr.right.accept(self)
