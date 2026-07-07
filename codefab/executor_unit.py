from codefab.ast_nodes import (
    Assign,
    Binary,
    BlockStmt,
    ExpressionStmt,
    ForStmt,
    Grouping,
    IfStmt,
    Literal,
    PrintStmt,
    Unary,
    Variable,
    VarStmt,
)
from codefab.tokens import TokenType


class ExecutorRuntimeError(Exception):
    def __init__(self, message: str, line: int = 1):
        super().__init__(message)
        self.message = message
        self.line = line


class Environment:
    def __init__(self, enclosing=None):
        self.values = {}
        self.enclosing = enclosing

    def define(self, lexeme: str, value) -> None:
        self.values[lexeme] = value

    def get(self, name_token):
        lexeme = name_token.lexeme

        if lexeme in self.values:
            return self.values[lexeme]

        if self.enclosing is not None:
            return self.enclosing.get(name_token)

        raise ExecutorRuntimeError(
            f"정의되지 않은 변수 '{lexeme}'입니다.",
            line=name_token.line,
        )

    def assign(self, name_token, value) -> None:
        lexeme = name_token.lexeme

        if lexeme in self.values:
            self.values[lexeme] = value
            return

        if self.enclosing is not None:
            self.enclosing.assign(name_token, value)
            return

        raise ExecutorRuntimeError(
            f"정의되지 않은 변수 '{lexeme}'입니다.",
            line=name_token.line,
        )


class ExecutorUnit:
    def __init__(self):
        self.environment = Environment()

    def execute(self, statements) -> None:
        for statement in statements:
            self._execute_stmt(statement)

    def _execute_stmt(self, statement) -> None:
        if isinstance(statement, PrintStmt):
            value = self._evaluate_expr(statement.expression)
            print(self._stringify(value))
            return

        if isinstance(statement, ExpressionStmt):
            self._evaluate_expr(statement.expression)
            return

        if isinstance(statement, VarStmt):
            value = None
            if statement.initializer is not None:
                value = self._evaluate_expr(statement.initializer)
            self.environment.define(statement.name.lexeme, value)
            return

        if isinstance(statement, BlockStmt):
            self._execute_block(statement.statements, Environment(self.environment))
            return

        if isinstance(statement, IfStmt):
            if self._is_truthy(self._evaluate_expr(statement.condition)):
                self._execute_stmt(statement.then_branch)
            elif statement.else_branch is not None:
                self._execute_stmt(statement.else_branch)
            return

        if isinstance(statement, ForStmt):
            if statement.initializer is not None:
                self._execute_stmt(statement.initializer)

            while statement.condition is None or self._is_truthy(
                self._evaluate_expr(statement.condition)
            ):
                self._execute_stmt(statement.body)
                if statement.increment is not None:
                    self._evaluate_expr(statement.increment)
            return

        raise ExecutorRuntimeError(
            f"지원하지 않는 Statement 입니다: {type(statement).__name__}",
            line=1,
        )

    def _execute_block(self, statements, environment: Environment) -> None:
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self._execute_stmt(statement)
        finally:
            self.environment = previous

    def _evaluate_expr(self, expression):
        if isinstance(expression, Literal):
            return expression.value

        if isinstance(expression, Variable):
            return self._look_up_variable(expression.name)

        if isinstance(expression, Assign):
            return self._evaluate_assign(expression)

        if isinstance(expression, Grouping):
            return self._evaluate_expr(expression.expression)

        if isinstance(expression, Unary):
            return self._evaluate_unary(expression)

        if isinstance(expression, Binary):
            return self._evaluate_binary(expression)

        raise ExecutorRuntimeError(
            f"지원하지 않는 Expression 입니다: {type(expression).__name__}",
            line=1,
        )

    def _look_up_variable(self, name_token):
        return self.environment.get(name_token)

    def _evaluate_assign(self, expression):
        value = self._evaluate_expr(expression.value)
        self.environment.assign(expression.name, value)
        return value

    def _is_truthy(self, value) -> bool:
        if value is None:
            return False

        if isinstance(value, bool):
            return value

        return True

    def _evaluate_unary(self, expression):
        right = self._evaluate_expr(expression.right)

        operator_type = expression.operator.type
        line = expression.operator.line

        if operator_type == TokenType.MINUS:
            if not isinstance(right, float):
                raise ExecutorRuntimeError(
                    "피연산자는 반드시 숫자여야 합니다.",
                    line=line,
                )
            return -right

        raise ExecutorRuntimeError(
            f"지원하지 않는 단항 연산자입니다: {expression.operator.lexeme}",
            line=line,
        )

    def _evaluate_binary(self, expression):
        left = self._evaluate_expr(expression.left)
        right = self._evaluate_expr(expression.right)

        operator_type = expression.operator.type
        line = expression.operator.line

        if operator_type == TokenType.PLUS:
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            if isinstance(left, float) and isinstance(right, float):
                return left + right
            raise ExecutorRuntimeError(
                "피연산자는 둘 다 숫자이거나 둘 다 문자열이어야 합니다.",
                line=line,
            )

        if operator_type == TokenType.MINUS:
            self._check_number_operands(left, right, line)
            return left - right

        if operator_type == TokenType.STAR:
            self._check_number_operands(left, right, line)
            return left * right

        if operator_type == TokenType.SLASH:
            self._check_number_operands(left, right, line)

            if right == 0:
                raise ExecutorRuntimeError("0으로 나눈 오류", line=line)

            return left / right

        if operator_type == TokenType.GREATER:
            self._check_number_operands(left, right, line)
            return left > right

        if operator_type == TokenType.GREATER_EQUAL:
            self._check_number_operands(left, right, line)
            return left >= right

        if operator_type == TokenType.LESS:
            self._check_number_operands(left, right, line)
            return left < right

        if operator_type == TokenType.LESS_EQUAL:
            self._check_number_operands(left, right, line)
            return left <= right

        if operator_type == TokenType.EQUAL_EQUAL:
            return left == right

        if operator_type == TokenType.BANG_EQUAL:
            return left != right

        raise ExecutorRuntimeError(
            f"지원하지 않는 이항 연산자입니다: {expression.operator.lexeme}",
            line=line,
        )

    def _check_number_operands(self, left, right, line: int) -> None:
        if not isinstance(left, float) or not isinstance(right, float):
            raise ExecutorRuntimeError(
                "피연산자는 반드시 숫자여야 합니다.",
                line=line,
            )

    def _stringify(self, value) -> str:
        if isinstance(value, bool):
            return "참" if value else "거짓"

        if isinstance(value, float) and value.is_integer():
            return str(int(value))

        return str(value)
