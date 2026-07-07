from codefab.ast_nodes import Binary, BlockStmt, ExpressionStmt, Stmt, Variable, VarStmt
from codefab.error import (
    DuplicateVariableError,
    SelfReferenceInInitializerError,
    UndeclaredVariableError,
)


class Checker:
    def __init__(self) -> None:
        self.scopes: list[set[str]] = [set()]
        self.initializing: str | None = None

    @property
    def declared(self) -> set[str]:
        return self.scopes[-1]

    def resolve(self, statements: list[Stmt]) -> None:
        for stmt in statements:
            stmt.accept(self)

    def visit_expression_stmt(self, stmt: ExpressionStmt) -> None:
        stmt.expression.accept(self)

    def visit_block_stmt(self, stmt: BlockStmt) -> None:
        self.scopes.append(set())
        for statement in stmt.statements:
            statement.accept(self)
        self.scopes.pop()

    def visit_var_stmt(self, stmt: VarStmt) -> None:
        if stmt.name.lexeme in self.scopes[-1]:
            raise DuplicateVariableError(stmt.name.line)
        if stmt.initializer is not None:
            self.initializing = stmt.name.lexeme
            stmt.initializer.accept(self)
            self.initializing = None
        self.scopes[-1].add(stmt.name.lexeme)

    def visit_variable(self, expr: Variable) -> None:
        if expr.name.lexeme == self.initializing:
            raise SelfReferenceInInitializerError(expr.name.line)
        if not any(expr.name.lexeme in scope for scope in self.scopes):
            raise UndeclaredVariableError(expr.name.line)

    def visit_binary(self, expr: Binary) -> None:
        expr.left.accept(self)
        expr.right.accept(self)
