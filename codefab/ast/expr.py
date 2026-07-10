from abc import ABC, abstractmethod
from dataclasses import dataclass

from codefab.common.tokens import Token


class Expr(ABC):
    @abstractmethod
    def accept(self, visitor): ...


# ---- Expr 노드 ----
@dataclass
class Literal(Expr):
    value: object  # float | str | bool | None
    line: int = 1

    def accept(self, visitor):
        return visitor.visit_literal(self)


@dataclass
class Variable(Expr):
    name: Token

    def accept(self, visitor):
        return visitor.visit_variable(self)


@dataclass
class Assign(Expr):
    name: Token
    value: Expr

    def accept(self, visitor):
        return visitor.visit_assign(self)


@dataclass
class Unary(Expr):
    operator: Token
    right: Expr

    def accept(self, visitor):
        return visitor.visit_unary(self)


@dataclass
class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr

    def accept(self, visitor):
        return visitor.visit_binary(self)


@dataclass
class Logical(Expr):  # and / or (단락 평가를 위해 Binary와 분리)
    left: Expr
    operator: Token
    right: Expr

    def accept(self, visitor):
        return visitor.visit_logical(self)


@dataclass
class Grouping(Expr):
    expression: Expr

    def accept(self, visitor):
        return visitor.visit_grouping(self)


@dataclass
class This(Expr):
    keyword: Token

    def accept(self, visitor):
        return visitor.visit_this(self)


@dataclass
class Super(Expr):
    keyword: Token
    method: Token

    def accept(self, visitor):
        return visitor.visit_super(self)


@dataclass
class Get(Expr):
    object: Expr
    name: Token

    def accept(self, visitor):
        return visitor.visit_get(self)


@dataclass
class Set(Expr):
    object: Expr
    name: Token
    value: Expr

    def accept(self, visitor):
        return visitor.visit_set(self)


@dataclass
class Call(Expr):
    callee: Expr
    paren: Token  # 오류 리포팅용 ')' 토큰
    arguments: list[Expr]

    def accept(self, visitor):
        return visitor.visit_call(self)


@dataclass
class InstanceOf(Expr):
    object: Expr
    klass: Expr

    def accept(self, visitor):
        return visitor.visit_instance_of(self)
