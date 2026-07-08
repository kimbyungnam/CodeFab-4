from abc import ABC, abstractmethod
from dataclasses import dataclass

from codefab.tokens import Token


class Expr(ABC):
    @abstractmethod
    def accept(self, visitor): ...


class Stmt(ABC):
    @abstractmethod
    def accept(self, visitor): ...


# ---- Expr 노드 ----
@dataclass
class Literal(Expr):
    value: object  # float | str | bool | None

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


# ---- Stmt 노드 ----
@dataclass
class ExpressionStmt(Stmt):
    expression: Expr

    def accept(self, visitor):
        return visitor.visit_expression_stmt(self)


@dataclass
class PrintStmt(Stmt):
    expression: Expr

    def accept(self, visitor):
        return visitor.visit_print_stmt(self)


@dataclass
class VarStmt(Stmt):
    name: Token
    initializer: Expr | None

    def accept(self, visitor):
        return visitor.visit_var_stmt(self)


@dataclass
class BlockStmt(Stmt):
    statements: list[Stmt]

    def accept(self, visitor):
        return visitor.visit_block_stmt(self)


@dataclass
class IfStmt(Stmt):
    condition: Expr
    then_branch: Stmt
    else_branch: Stmt | None

    def accept(self, visitor):
        return visitor.visit_if_stmt(self)


@dataclass
class ForStmt(Stmt):
    initializer: Stmt | None  # VarStmt | ExpressionStmt | None
    condition: Expr | None
    increment: Expr | None
    body: Stmt

    def accept(self, visitor):
        return visitor.visit_for_stmt(self)


# ---- 함수 관련 추가 노드 ----
@dataclass
class Call(Expr):
    callee: Expr
    paren: Token  # 인자 목록을 닫는 ')' 토큰. 런타임 에러 라인 리포팅용
    arguments: list[Expr]

    def accept(self, visitor):
        return visitor.visit_call(self)


@dataclass
class FunctionStmt(Stmt):
    name: Token
    params: list[Token]
    body: list[Stmt]

    def accept(self, visitor):
        return visitor.visit_function_stmt(self)


@dataclass
class ReturnStmt(Stmt):
    keyword: Token  # '반환' 토큰. 함수 외부 사용 에러 라인 리포팅용
    value: Expr | None

    def accept(self, visitor):
        return visitor.visit_return_stmt(self)
