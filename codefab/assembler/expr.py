from dataclasses import dataclass

from codefab.assembler.tokens import Token


class Expr: ...


@dataclass(frozen=True)
class Literal(Expr):
    value: object


@dataclass(frozen=True)
class Variable(Expr):
    name: Token


@dataclass(frozen=True)
class Assign(Expr):
    name: Token
    value: Expr


@dataclass(frozen=True)
class Binary(Expr):
    left: Expr
    operator: Token
    right: Expr


@dataclass(frozen=True)
class Unary(Expr):
    operator: Token
    right: Expr


@dataclass(frozen=True)
class Logical(Expr):
    left: Expr
    operator: Token
    right: Expr


@dataclass(frozen=True)
class Grouping(Expr):
    expression: Expr
