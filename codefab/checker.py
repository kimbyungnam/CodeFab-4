from enum import Enum, auto

from codefab.ast_nodes import (
    Assign,
    Binary,
    BlockStmt,
    Call,
    ClassStmt,
    ExpressionStmt,
    ForStmt,
    Get,
    Grouping,
    IfStmt,
    InstanceOf,
    Literal,
    Logical,
    PrintStmt,
    Set,
    Stmt,
    Super,
    This,
    Unary,
    Variable,
    VarStmt,
)
from codefab.error import (
    DuplicateVariableError,
    SelfInheritanceError,
    SelfReferenceInInitializerError,
    SuperOutsideClassError,
    SuperWithoutSuperclassError,
    ThisOutsideClassError,
)


class _ClassContext(Enum):
    NONE = auto()
    CLASS = auto()
    SUBCLASS = auto()


class Checker:
    def __init__(self):
        self.scopes: list[set[str]] = [set()]
        self.initializing: str | None = None
        self.current_class = _ClassContext.NONE

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

    def visit_class_stmt(self, stmt: ClassStmt):
        if (
            stmt.superclass is not None
            and stmt.superclass.name.lexeme == stmt.name.lexeme
        ):
            raise SelfInheritanceError(stmt.name.line)

        if stmt.superclass is not None:
            stmt.superclass.accept(self)

        enclosing_class = self.current_class
        if stmt.superclass is not None:
            self.current_class = _ClassContext.SUBCLASS
        else:
            self.current_class = _ClassContext.CLASS

        for method in stmt.methods:
            self.scopes.append(set())
            for statement in method.body:
                statement.accept(self)
            self.scopes.pop()

        self.current_class = enclosing_class

    def visit_this(self, expr: This):
        if self.current_class == _ClassContext.NONE:
            raise ThisOutsideClassError(expr.keyword.line)

    def visit_super(self, expr: Super):
        if self.current_class == _ClassContext.NONE:
            raise SuperOutsideClassError(expr.keyword.line)
        if self.current_class != _ClassContext.SUBCLASS:
            raise SuperWithoutSuperclassError(expr.keyword.line)

    def visit_get(self, expr: Get):
        expr.object.accept(self)

    def visit_set(self, expr: Set):
        expr.object.accept(self)
        expr.value.accept(self)

    def visit_call(self, expr: Call):
        expr.callee.accept(self)
        for argument in expr.arguments:
            argument.accept(self)

    def visit_instance_of(self, expr: InstanceOf):
        expr.object.accept(self)
        expr.klass.accept(self)

    # ---- 정적 배열 (codefab/array_nodes.py) ----

    def visit_array_literal(self, expr):
        expr.size.accept(self)

    def visit_index_get(self, expr):
        expr.target.accept(self)
        expr.index.accept(self)

    def visit_index_set(self, expr):
        expr.target.accept(self)
        expr.index.accept(self)
        expr.value.accept(self)
