"""Expr/Stmt(codefab/ast/expr.py, codefab/ast/stmt.py, codefab/ast/array.py)를 방문하는 모든
Visitor가 구현해야 하는 인터페이스.

새 Element(Expr/Stmt 서브클래스)를 추가할 때는 여기에 대응하는 visit_* 를
같이 추가해야 한다 — 누락 시 tests/test_visitor_sync.py 가 실패한다.
"""

from abc import ABC, abstractmethod


class Visitor(ABC):
    # ---- Expr (codefab/ast/expr.py) ----
    @abstractmethod
    def visit_literal(self, expr): ...

    @abstractmethod
    def visit_variable(self, expr): ...

    @abstractmethod
    def visit_assign(self, expr): ...

    @abstractmethod
    def visit_unary(self, expr): ...

    @abstractmethod
    def visit_binary(self, expr): ...

    @abstractmethod
    def visit_logical(self, expr): ...

    @abstractmethod
    def visit_grouping(self, expr): ...

    @abstractmethod
    def visit_this(self, expr): ...

    @abstractmethod
    def visit_super(self, expr): ...

    @abstractmethod
    def visit_get(self, expr): ...

    @abstractmethod
    def visit_set(self, expr): ...

    @abstractmethod
    def visit_call(self, expr): ...

    @abstractmethod
    def visit_instance_of(self, expr): ...

    # ---- Stmt (codefab/ast/stmt.py) ----
    @abstractmethod
    def visit_expression_stmt(self, stmt): ...

    @abstractmethod
    def visit_print_stmt(self, stmt): ...

    @abstractmethod
    def visit_var_stmt(self, stmt): ...

    @abstractmethod
    def visit_block_stmt(self, stmt): ...

    @abstractmethod
    def visit_if_stmt(self, stmt): ...

    @abstractmethod
    def visit_for_stmt(self, stmt): ...

    @abstractmethod
    def visit_function_stmt(self, stmt): ...

    @abstractmethod
    def visit_return_stmt(self, stmt): ...

    @abstractmethod
    def visit_class_stmt(self, stmt): ...

    @abstractmethod
    def visit_import_stmt(self, stmt): ...

    # ---- Expr (codefab/ast/array.py) ----
    @abstractmethod
    def visit_array_literal(self, expr): ...

    @abstractmethod
    def visit_index_get(self, expr): ...

    @abstractmethod
    def visit_index_set(self, expr): ...
