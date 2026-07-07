from codefab.assembler.expr import Assign, Binary, Literal, Variable
from codefab.ast_nodes import BlockStmt, ForStmt, IfStmt, PrintStmt, VarStmt
from codefab.tokens import TokenType


class ExecutorRuntimeError(Exception):
    def __init__(self, message: str, line: int = 1):
        super().__init__(message)
        self.message = message
        self.line = line


class ExecutorUnit:
    def __init__(self):
        self.environment = {}

    def execute(self, statements) -> None:
        for statement in statements:
            self._execute_stmt(statement)

    def _execute_stmt(self, statement) -> None:
        if isinstance(statement, PrintStmt):
            value = self._evaluate_expr(statement.expression)
            print(self._stringify(value))
            return

        if isinstance(statement, VarStmt):
            value = None
            if statement.initializer is not None:
                value = self._evaluate_expr(statement.initializer)
            self.environment[statement.name.lexeme] = value
            return

        if isinstance(statement, BlockStmt):
            for inner_statement in statement.statements:
                self._execute_stmt(inner_statement)
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

    def _evaluate_expr(self, expression):
        if isinstance(expression, Literal):
            return expression.value

        if isinstance(expression, Variable):
            return self._look_up_variable(expression.name)

        if isinstance(expression, Assign):
            return self._evaluate_assign(expression)

        if isinstance(expression, Binary):
            return self._evaluate_binary(expression)

        raise ExecutorRuntimeError(
            f"지원하지 않는 Expression 입니다: {type(expression).__name__}",
            line=1,
        )

    def _look_up_variable(self, name_token):
        lexeme = name_token.lexeme
        line = name_token.line

        if lexeme not in self.environment:
            raise ExecutorRuntimeError(
                f"정의되지 않은 변수 '{lexeme}'입니다.",
                line=line,
            )

        return self.environment[lexeme]

    def _evaluate_assign(self, expression):
        value = self._evaluate_expr(expression.value)
        lexeme = expression.name.lexeme
        line = expression.name.line

        if lexeme not in self.environment:
            raise ExecutorRuntimeError(
                f"정의되지 않은 변수 '{lexeme}'입니다.",
                line=line,
            )

        self.environment[lexeme] = value
        return value

    def _is_truthy(self, value) -> bool:
        if value is None:
            return False

        if isinstance(value, bool):
            return value

        return True

    def _evaluate_binary(self, expression):
        left = self._evaluate_expr(expression.left)
        right = self._evaluate_expr(expression.right)

        operator_type = expression.operator.type
        line = expression.operator.line

        if operator_type == TokenType.PLUS:
            self._check_number_operands(left, right, line)
            return left + right

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
        if isinstance(value, float) and value.is_integer():
            return str(int(value))

        return str(value)
