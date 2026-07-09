from codefab.ast import Assign, Variable
from codefab.executor.executor import Environment, ExecutorUnit


class OptimizedExecutorUnit(ExecutorUnit):
    """Resolver 가 부착한 distance 를 이용해 변수 조회를 O(1)로 처리하는 Executor.

    ExecutorUnit이 Variable/Assign 을 만나면 visit_variable/visit_assign 을
    통해 self._look_up_variable(expr.name) / self._evaluate_assign(expr) 로
    넘기는데, 그 호출부는 Token 만 넘겨서(Expr 노드 자체를 안 넘겨서) distance
    를 조회할 수 없다. 그래서 executor/executor.py 를 고치는 대신, 이 서브클래스가
    visit_variable/visit_assign 두 메서드만 오버라이드해서 distance 가 붙어있는
    경우를 먼저 처리하고, 없으면 super() 로 위임한다 (codefab/executor/function_executor.py 의
    FunctionExecutorUnit 과 동일한 패턴).

    Environment.values / .enclosing 이 이미 public 이라 Environment 클래스도
    건드릴 필요 없이 여기서 직접 몇 단계 위로 올라갈지 계산해서 접근한다.
    """

    def visit_variable(self, expr: Variable):
        distance = getattr(expr, "distance", None)
        if distance is not None:
            return self._ancestor(distance).values[expr.name.lexeme]
        return super().visit_variable(expr)

    def visit_assign(self, expr: Assign):
        distance = getattr(expr, "distance", None)
        if distance is not None:
            value = self._evaluate_expr(expr.value)
            self._ancestor(distance).values[expr.name.lexeme] = value
            return value
        return super().visit_assign(expr)

    def _ancestor(self, distance: int) -> Environment:
        environment = self.environment
        for _ in range(distance):
            environment = environment.enclosing
        return environment
