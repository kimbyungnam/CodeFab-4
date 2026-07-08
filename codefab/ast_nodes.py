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


@dataclass
class MethodDecl:
    """클래스 본문에 선언된 메서드 하나. Stmt가 아닌 순수 데이터로,
    ClassStmt가 목록으로 보관하며 별도로 accept 되지 않는다."""

    name: Token
    params: list[Token]
    body: list[Stmt]


@dataclass
class ClassStmt(Stmt):
    name: Token
    superclass: Variable | None
    methods: list[MethodDecl]

    def accept(self, visitor):
        return visitor.visit_class_stmt(self)
class ImportStmt(Stmt):
    path: Token  # STRING 토큰, path.literal 이 실제 파일 경로 문자열
    alias: Token  # IDENTIFIER 토큰

    def accept(self, visitor):
        return visitor.visit_import_stmt(self)


@dataclass
class MethodDecl:
    """클래스 본문에 선언된 메서드 하나. Stmt가 아닌 순수 데이터로,
    ClassStmt가 목록으로 보관하며 별도로 accept 되지 않는다."""

    name: Token
    params: list[Token]
    body: list[Stmt]


@dataclass
class ClassStmt(Stmt):
    name: Token
    superclass: Variable | None
    methods: list[MethodDecl]

    def accept(self, visitor):
        return visitor.visit_class_stmt(self)
