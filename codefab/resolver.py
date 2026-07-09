from codefab.ast import Assign, Variable
from codefab.checker import Checker
from codefab.executor import Environment, ExecutorUnit


class Resolver(Checker):
    """지역 변수 참조에 정적 바인딩(distance)을 부착하는 Checker 확장.

    Checker 를 상속해서 스코프 추적(self.scopes)과 기존 검증(중복 선언,
    자기참조 등)을 그대로 재사용한다. visit_variable / visit_assign 두
    메서드만 오버라이드해서, 기존 검증 뒤에 "몇 단계 위 스코프에 있는지"
    (distance) 를 계산해 해당 Expr 노드에 동적으로 얹어둔다.

    - codefab/ast/expr.py, codefab/ast/stmt.py, codefab/checker.py 는 전혀 건드리지 않는다
      (distance 는 dataclass 필드가 아니라 side-channel attribute).
    - 전역 변수(self.scopes[0])는 일부러 대상에서 제외한다. REPL 에서 전역
      변수를 나중에 선언/재선언해도 깨지지 않도록, 전역은 항상 기존 동적
      조회(Environment.get/assign)로 폴백시키기 위함이다.
    - distance 를 못 찾은 경우(예: 전역 변수)에는 아무 것도 붙이지 않는다.
      Executor 쪽에서 `getattr(expr, "distance", None)` 로 조회해서 없으면
      기존 방식대로 동작하면 된다.
    """

    def visit_variable(self, expr: Variable):
        super().visit_variable(expr)
        self._bind_distance(expr, expr.name.lexeme)

    def visit_assign(self, expr: Assign):
        super().visit_assign(expr)
        self._bind_distance(expr, expr.name.lexeme)

    def _bind_distance(self, expr, lexeme: str) -> None:
        local_scopes = self.scopes[1:]  # scopes[0] 은 global, 정적 바인딩 제외
        for distance, scope in enumerate(reversed(local_scopes)):
            if lexeme in scope:
                expr.distance = distance
                return


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
