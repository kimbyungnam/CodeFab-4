"""리터럴 상수 연산 폴딩(Constant Folding) 최적화.

`Checker`처럼 예외로 검증하는 게 아니라 트리 자체를 변형해야 해서
(부모 노드의 필드를 새 값으로 교체) Checker 를 상속하지 않고 독립적인
Visitor 로 구현한다. codefab/ast_nodes.py, codefab/checker.py,
codefab/executor_unit.py 는 전혀 건드리지 않는다.

핵심 규칙: 실행 시 에러가 나야 하는 경우(타입 불일치, 0으로 나누기 등)는
절대 접지 않고 원본 그대로 둔다. 그래야 나중에 Checker/Executor 가 원래
내야 할 에러를 그대로 낸다 — Optimizer 가 에러 여부를 대신 판단하지 않는다.
"""

from codefab.array_nodes import ArrayLiteral, IndexGet, IndexSet
from codefab.ast_nodes import (
    Assign,
    Binary,
    BlockStmt,
    Call,
    ClassStmt,
    Expr,
    ExpressionStmt,
    ForStmt,
    FunctionStmt,
    Get,
    Grouping,
    IfStmt,
    Literal,
    Logical,
    PrintStmt,
    ReturnStmt,
    Set,
    Stmt,
    Unary,
    VarStmt,
)
from codefab.tokens import TokenType


class Optimizer:
    def optimize(self, statements: list[Stmt]) -> None:
        for stmt in statements:
            self._optimize_stmt(stmt)

    # ---------------- Stmt ----------------

    def _optimize_stmt(self, stmt: Stmt) -> None:
        if isinstance(stmt, ExpressionStmt):
            stmt.expression = self._optimize_expr(stmt.expression)
            return

        if isinstance(stmt, PrintStmt):
            stmt.expression = self._optimize_expr(stmt.expression)
            return

        if isinstance(stmt, VarStmt):
            if stmt.initializer is not None:
                stmt.initializer = self._optimize_expr(stmt.initializer)
            return

        if isinstance(stmt, BlockStmt):
            for inner in stmt.statements:
                self._optimize_stmt(inner)
            return

        if isinstance(stmt, IfStmt):
            stmt.condition = self._optimize_expr(stmt.condition)
            self._optimize_stmt(stmt.then_branch)
            if stmt.else_branch is not None:
                self._optimize_stmt(stmt.else_branch)
            return

        if isinstance(stmt, ForStmt):
            if stmt.initializer is not None:
                self._optimize_stmt(stmt.initializer)
            if stmt.condition is not None:
                stmt.condition = self._optimize_expr(stmt.condition)
            if stmt.increment is not None:
                stmt.increment = self._optimize_expr(stmt.increment)
            self._optimize_stmt(stmt.body)
            return

        if isinstance(stmt, FunctionStmt):
            for inner in stmt.body:
                self._optimize_stmt(inner)
            return

        if isinstance(stmt, ReturnStmt):
            if stmt.value is not None:
                stmt.value = self._optimize_expr(stmt.value)
            return

        if isinstance(stmt, ClassStmt):
            for method in stmt.methods:
                for inner in method.body:
                    self._optimize_stmt(inner)
            return

        # 그 외(다른 팀 브랜치의 import Stmt 등)는 이번 범위 밖이라
        # 손대지 않고 그대로 둔다.

    # ---------------- Expr ----------------

    def _optimize_expr(self, expr: Expr) -> Expr:
        if isinstance(expr, Grouping):
            expr.expression = self._optimize_expr(expr.expression)
            if isinstance(expr.expression, Literal):
                return expr.expression
            return expr

        if isinstance(expr, Unary):
            expr.right = self._optimize_expr(expr.right)
            return self._fold_unary(expr)

        if isinstance(expr, Binary):
            expr.left = self._optimize_expr(expr.left)
            expr.right = self._optimize_expr(expr.right)
            return self._fold_binary(expr)

        if isinstance(expr, Logical):
            expr.left = self._optimize_expr(expr.left)
            expr.right = self._optimize_expr(expr.right)
            return expr  # 단락평가 의미가 있어 이번 범위에서는 접지 않는다

        if isinstance(expr, Assign):
            expr.value = self._optimize_expr(expr.value)
            return expr

        if isinstance(expr, ArrayLiteral):
            expr.size = self._optimize_expr(expr.size)
            return expr

        if isinstance(expr, IndexGet):
            expr.target = self._optimize_expr(expr.target)
            expr.index = self._optimize_expr(expr.index)
            return expr

        if isinstance(expr, IndexSet):
            expr.target = self._optimize_expr(expr.target)
            expr.index = self._optimize_expr(expr.index)
            expr.value = self._optimize_expr(expr.value)
            return expr

        if isinstance(expr, Call):
            expr.callee = self._optimize_expr(expr.callee)
            expr.arguments = [
                self._optimize_expr(argument) for argument in expr.arguments
            ]
            return expr

        if isinstance(expr, Get):
            expr.object = self._optimize_expr(expr.object)
            return expr

        if isinstance(expr, Set):
            expr.object = self._optimize_expr(expr.object)
            expr.value = self._optimize_expr(expr.value)
            return expr

        return expr  # Literal, Variable 등은 더 접을 게 없다

    def _fold_unary(self, expr: Unary) -> Expr:
        if not isinstance(expr.right, Literal):
            return expr

        value = expr.right.value
        if expr.operator.type == TokenType.MINUS and isinstance(value, float):
            return Literal(-value)
        if expr.operator.type == TokenType.BANG:
            return Literal(not self._is_truthy(value))
        return expr

    def _fold_binary(self, expr: Binary) -> Expr:
        if not isinstance(expr.left, Literal) or not isinstance(expr.right, Literal):
            return expr

        left, right = expr.left.value, expr.right.value
        op = expr.operator.type

        if op == TokenType.PLUS:
            if isinstance(left, float) and isinstance(right, float):
                return Literal(left + right)
            if isinstance(left, str) and isinstance(right, str):
                return Literal(left + right)
            return expr  # 타입 불일치 -> 실행 시 에러가 나야 하므로 그대로 둔다

        if op == TokenType.EQUAL_EQUAL:
            return Literal(left == right)
        if op == TokenType.BANG_EQUAL:
            return Literal(left != right)

        if not (isinstance(left, float) and isinstance(right, float)):
            # 나머지 연산자는 전부 숫자 전용 -> 숫자가 아니면 실행 시 에러가
            # 나야 하므로 그대로 둔다.
            return expr

        if op == TokenType.MINUS:
            return Literal(left - right)
        if op == TokenType.STAR:
            return Literal(left * right)
        if op == TokenType.SLASH:
            if right == 0:
                return expr  # 0으로 나눔 -> 실행 시점 에러로 남겨둔다
            return Literal(left / right)
        if op == TokenType.GREATER:
            return Literal(left > right)
        if op == TokenType.GREATER_EQUAL:
            return Literal(left >= right)
        if op == TokenType.LESS:
            return Literal(left < right)
        if op == TokenType.LESS_EQUAL:
            return Literal(left <= right)

        return expr

    def _is_truthy(self, value: object) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        return True
