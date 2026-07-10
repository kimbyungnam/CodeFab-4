"""정적 배열(Array) 관련 Expr 노드.

기존 codefab/ast/expr.py 는 건드리지 않고, 같은 Expr 베이스와 Visitor 규약
(accept(visitor) -> visitor.visit_xxx(self))을 그대로 따르는 노드를 별도 파일에 추가한다.
Checker/ExecutorUnit 에 대응하는 visit_array_literal / visit_index_get / visit_index_set
를 구현해야 실제로 방문할 수 있다.
"""

from dataclasses import dataclass

from codefab.ast.expr import Expr


@dataclass
class ArrayLiteral(Expr):
    """Array(size) — 크기가 size 인 배열을 생성한다."""

    size: Expr
    line: int

    def accept(self, visitor):
        return visitor.visit_array_literal(self)


@dataclass
class IndexGet(Expr):
    """target[index] — 배열 읽기."""

    target: Expr
    index: Expr
    line: int

    def accept(self, visitor):
        return visitor.visit_index_get(self)


@dataclass
class IndexSet(Expr):
    """target[index] = value — 배열 쓰기."""

    target: Expr
    index: Expr
    value: Expr
    line: int

    def accept(self, visitor):
        return visitor.visit_index_set(self)
