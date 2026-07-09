from codefab.ast import Assign, Variable
from codefab.checker.checker import Checker


class Resolver(Checker):
    """지역 변수 참조에 정적 바인딩(distance)을 부착하는 Checker 확장.

    Checker 를 상속해서 스코프 추적(self.scopes)과 기존 검증(중복 선언,
    자기참조 등)을 그대로 재사용한다. visit_variable / visit_assign 두
    메서드만 오버라이드해서, 기존 검증 뒤에 "몇 단계 위 스코프에 있는지"
    (distance) 를 계산해 해당 Expr 노드에 동적으로 얹어둔다.

    - codefab/ast/expr.py, codefab/ast/stmt.py, codefab/checker/checker.py 는 전혀 건드리지 않는다
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
