from codefab.interpreter import Interpreter
from codefab.optimizer import Optimizer
from codefab.resolver import OptimizedExecutorUnit, Resolver


class OptimizingChecker(Resolver):
    """검증(Checker) + 정적 바인딩(Resolver) + 상수 폴딩(Optimizer)을 한 번에 수행한다.

    Interpreter 는 checker 하나만 주입받을 수 있으므로, 그 자리에 검증/바인딩/
    폴딩을 순서대로 실행하는 이 클래스를 끼워 넣는다. interpreter.py 는 전혀
    건드리지 않는다.
    """

    def resolve(self, statements) -> None:
        super().resolve(statements)  # 기존 검증 + distance 부착
        Optimizer().optimize(statements)  # 상수 폴딩 (트리 제자리 변형)


def create_optimized_interpreter() -> Interpreter:
    """정적 배열 + 실행 전 최적화(정적 바인딩, 상수 폴딩)가 적용된 Interpreter."""
    return Interpreter(
        checker=OptimizingChecker(),
        executor=OptimizedExecutorUnit(),
    )
