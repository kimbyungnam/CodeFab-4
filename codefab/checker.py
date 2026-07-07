from codefab.ast_nodes import (
    Assign,
    Binary,
    BlockStmt,
    ExpressionStmt,
    ForStmt,
    Grouping,
    IfStmt,
    Literal,
    Logical,
    PrintStmt,
    Stmt,
    Unary,
    Variable,
    VarStmt,
)
from codefab.error import DuplicateVariableError, SelfReferenceInInitializerError


class Checker:
    def __init__(self):
        self.scopes: list[set[str]] = [set()]
        self.initializing: str | None = None

    @property
    def declared(self) -> set[str]:
        return self.scopes[-1]

    def resolve(self, statements: list[Stmt]):
        for stmt in statements:
            stmt.accept(self)

    def visit_expression_stmt(self, stmt: ExpressionStmt):
        stmt.expression.accept(self)

    def visit_block_stmt(self, stmt: BlockStmt):
        self.scopes.append(set())
        for statement in stmt.statements:
            statement.accept(self)
        self.scopes.pop()

    def visit_var_stmt(self, stmt: VarStmt):
        if stmt.name.lexeme in self.scopes[-1]:
            raise DuplicateVariableError(stmt.name.line)
        if stmt.initializer is not None:
            self.initializing = stmt.name.lexeme
            stmt.initializer.accept(self)
            self.initializing = None
        self.scopes[-1].add(stmt.name.lexeme)

    def visit_variable(self, expr: Variable):
        if expr.name.lexeme == self.initializing:
            raise SelfReferenceInInitializerError(expr.name.line)

    def visit_binary(self, expr: Binary):
        expr.left.accept(self)
        expr.right.accept(self)

    def visit_literal(self, expr: Literal):
        pass

    def visit_grouping(self, expr: Grouping):
        expr.expression.accept(self)

    def visit_unary(self, expr: Unary):
        expr.right.accept(self)

    def visit_logical(self, expr: Logical):
        expr.left.accept(self)
        expr.right.accept(self)

    def visit_assign(self, expr: Assign):
        expr.value.accept(self)

    def visit_print_stmt(self, stmt: PrintStmt):
        stmt.expression.accept(self)

    def visit_if_stmt(self, stmt: IfStmt):
        stmt.condition.accept(self)
        stmt.then_branch.accept(self)
        if stmt.else_branch is not None:
            stmt.else_branch.accept(self)

    def visit_for_stmt(self, stmt: ForStmt):
        if stmt.initializer is not None:
            stmt.initializer.accept(self)
        if stmt.condition is not None:
            stmt.condition.accept(self)
        if stmt.increment is not None:
            stmt.increment.accept(self)
        stmt.body.accept(self)
