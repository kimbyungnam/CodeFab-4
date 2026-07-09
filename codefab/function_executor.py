from codefab.ast_nodes import Call, Expr, FunctionStmt, ReturnStmt, Stmt
from codefab.error import ArgumentCountMismatchError, NotCallableError
from codefab.executor_unit import Environment, ExecutorUnit, LaughClass, LaughFunction


class ReturnSignal(Exception):
    """'반환' 실행을 함수 호출 지점까지 되감기 위한 내부 제어 흐름 신호.

    사용자에게 노출되는 에러가 아니므로 codefab.error의 CodeFabError 계열이 아닌
    별도의 예외로 둔다.
    """

    def __init__(self, value: object):
        self.value = value


class UserFunction:
    """Laugh Language에서 '함수'로 선언된 값의 런타임 표현."""

    def __init__(
        self,
        declaration: FunctionStmt,
        closure: Environment,
        executor: "FunctionExecutorUnit",
    ):
        self.declaration = declaration
        self.closure = closure
        self._executor = executor

    @property
    def arity(self) -> int:
        return len(self.declaration.params)

    def call(self, arguments: list[object]) -> object:
        call_environment = Environment(self.closure)
        for param, argument in zip(self.declaration.params, arguments):
            call_environment.define(param.lexeme, argument)

        try:
            self._executor._execute_block(self.declaration.body, call_environment)
        except ReturnSignal as signal:
            return signal.value
        return None


class FunctionExecutorUnit(ExecutorUnit):
    """ExecutorUnit에 함수 선언 실행, 함수 호출, '반환' 처리를 추가한다.

    ExecutorUnit.execute()/`_execute_block()`은 전부 `self._execute_stmt(...)`,
    `self._evaluate_expr(...)`를 통해 서로를 호출하므로, 이 두 메서드만
    오버라이드하면(처리 못 하는 노드는 `super()`로 위임) 기존 executor_unit.py는
    전혀 건드리지 않고 함수 지원을 끼워 넣을 수 있다. 다만 클래스 메서드 호출은
    base `ExecutorUnit._call`/`_invoke_function` 경로(생성자 포함)를 그대로
    타므로, `_invoke_function`도 오버라이드해서 `ReturnSignal`이 이 경로에서도
    잡히도록 한다 — 그렇지 않으면 메서드 안의 '반환'이 값으로 변환되지 못하고
    호출 스택 최상단까지 새어나가 `Interpreter.interpret()`에 에러로 오인 처리된다.
    """

    def _execute_stmt(self, statement: Stmt):
        if isinstance(statement, FunctionStmt):
            function = UserFunction(statement, self.environment, self)
            self.environment.define(statement.name.lexeme, function)
            return

        if isinstance(statement, ReturnStmt):
            value = None
            if statement.value is not None:
                value = self._evaluate_expr(statement.value)
            raise ReturnSignal(value)

        super()._execute_stmt(statement)

    def _evaluate_expr(self, expression: Expr) -> object:
        if isinstance(expression, Call):
            return self._evaluate_call(expression)

        return super()._evaluate_expr(expression)

    def _invoke_function(
        self, function: LaughFunction, arguments: list[object]
    ) -> object:
        try:
            return super()._invoke_function(function, arguments)
        except ReturnSignal as signal:
            return signal.value

    def _evaluate_call(self, expression: Call) -> object:
        callee = self._evaluate_expr(expression.callee)
        arguments = [self._evaluate_expr(argument) for argument in expression.arguments]

        if isinstance(callee, UserFunction):
            if len(arguments) != callee.arity:
                raise ArgumentCountMismatchError(
                    expected=callee.arity,
                    actual=len(arguments),
                    line=expression.paren.line,
                )
            return callee.call(arguments)

        if isinstance(callee, (LaughClass, LaughFunction)):
            return self._call(callee, arguments)

        raise NotCallableError(line=expression.paren.line)
