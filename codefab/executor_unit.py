class ExecutorRuntimeError(Exception):
    def __init__(self, message: str, line: int = 1):
        super().__init__(message)
        self.message = message
        self.line = line


class ExecutorUnit:
    def execute(self, statements) -> None:
        for statement in statements:
            self._execute_stmt(statement)

    def _execute_stmt(self, statement) -> None:
        node_type = statement.__class__.__name__

        if node_type == "PrintStmt":
            value = self._evaluate_expr(statement.expression)
            print(self._stringify(value))
            return

        raise ExecutorRuntimeError(
            f"지원하지 않는 Statement 입니다: {node_type}",
            line=1,
        )

    def _evaluate_expr(self, expression):
        node_type = expression.__class__.__name__

        if node_type == "Literal":
            return expression.value

        if node_type == "Binary":
            return self._evaluate_binary(expression)

        raise ExecutorRuntimeError(
            f"지원하지 않는 Expression 입니다: {node_type}",
            line=1,
        )

    def _evaluate_binary(self, expression):
        left = self._evaluate_expr(expression.left)
        right = self._evaluate_expr(expression.right)

        operator = expression.operator.lexeme
        line = getattr(expression.operator, "line", 1)

        if operator == "+":
            self._check_number_operands(left, right, line)
            return left + right

        if operator == "-":
            self._check_number_operands(left, right, line)
            return left - right

        if operator == "*":
            self._check_number_operands(left, right, line)
            return left * right

        if operator == "/":
            self._check_number_operands(left, right, line)

            if right == 0:
                raise ExecutorRuntimeError("0으로 나눈 오류", line=line)

            return left / right

        raise ExecutorRuntimeError(
            f"지원하지 않는 이항 연산자입니다: {operator}",
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
