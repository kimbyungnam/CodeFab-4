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
    ImportStmt,
    InstanceOf,
    Literal,
    Logical,
    PrintStmt,
    ReturnStmt,
    Set,
    Stmt,
    Super,
    This,
    Unary,
    Variable,
    VarStmt,
)
from codefab.error import (
    DuplicateImportError,
    DuplicateVariableError,
    ImportInsideLoopError,
    ReturnInInitializerError,
    SelfInheritanceError,
    SelfReferenceInInitializerError,
    SuperOutsideClassError,
    SuperWithoutSuperclassError,
    ThisOutsideClassError,
)
from codefab.module_loader import ModuleLoader

_INIT_METHOD_NAMES = ("init", "생성자")


class _ClassContext(Enum):
    NONE = auto()
    CLASS = auto()
    SUBCLASS = auto()


class Checker:
    def __init__(self, module_loader: ModuleLoader | None = None):
        self.scopes: list[set[str]] = [set()]
        self.imported_paths: list[set] = [set()]
        self.initializing: str | None = None
        self.current_class = _ClassContext.NONE
        self.loop_depth = 0
        self._module_loader = (
            module_loader if module_loader is not None else ModuleLoader()
        )
        self.in_initializer = False

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
        self.imported_paths.append(set())
        try:
            for statement in stmt.statements:
                statement.accept(self)
        finally:
            self.scopes.pop()
            self.imported_paths.pop()

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
        self.loop_depth += 1
        try:
            stmt.body.accept(self)
        finally:
            self.loop_depth -= 1

    def visit_import_stmt(self, stmt: ImportStmt):
        if self.loop_depth > 0:
            raise ImportInsideLoopError(stmt.path.line)
        if stmt.alias.lexeme in self.scopes[-1]:
            raise DuplicateVariableError(stmt.alias.line)

        resolved_path = self._module_loader.resolve(stmt.path.literal)
        if any(resolved_path in scope for scope in self.imported_paths):
            raise DuplicateImportError(stmt.path.literal, stmt.path.line)

        self._module_loader.load(resolved_path, referencing_line=stmt.path.line)

        self.imported_paths[-1].add(resolved_path)
        self.scopes[-1].add(stmt.alias.lexeme)

    def visit_class_stmt(self, stmt: ClassStmt):
        enclosing_class = self.current_class
        self.current_class = _ClassContext.CLASS

        if stmt.superclass is not None:
            if stmt.superclass.name.lexeme == stmt.name.lexeme:
                raise SelfInheritanceError(stmt.name.line)
            stmt.superclass.accept(self)
            self.current_class = _ClassContext.SUBCLASS

        enclosing_initializer = self.in_initializer
        for method in stmt.methods:
            self.in_initializer = method.name.lexeme in _INIT_METHOD_NAMES
            self.scopes.append(set())
            for statement in method.body:
                statement.accept(self)
            self.scopes.pop()
        self.in_initializer = enclosing_initializer

        self.current_class = enclosing_class

    def visit_return_stmt(self, stmt: ReturnStmt):
        if self.in_initializer:
            raise ReturnInInitializerError(stmt.keyword.line)
        if stmt.value is not None:
            stmt.value.accept(self)

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
