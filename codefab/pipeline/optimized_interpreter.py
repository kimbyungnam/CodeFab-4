from codefab.assembler.function_assembler import FunctionAssembler
from codefab.checker import FunctionChecker, Resolver
from codefab.common.optimizer import Optimizer
from codefab.executor import FunctionExecutorUnit, OptimizedExecutorUnit
from codefab.pipeline.interpreter import Interpreter


class OptimizingChecker(Resolver, FunctionChecker):
    """검증(Checker) + 함수 지원(FunctionChecker) + 정적 바인딩(Resolver) +
    상수 폴딩(Optimizer)을 한 번에 수행한다.

    Resolver와 FunctionChecker는 서로 다른 visit_* 메서드만 오버라이드하므로
    (Resolver: visit_variable/visit_assign, FunctionChecker:
    visit_function_stmt/visit_return_stmt/visit_call) 다중 상속으로 그대로
    합쳐진다. Interpreter는 checker 하나만 주입받을 수 있으므로, 그 자리에
    검증/함수지원/바인딩/폴딩을 순서대로 실행하는 이 클래스를 끼워 넣는다.
    """

    def resolve(self, statements) -> None:
        super().resolve(statements)  # 기존 검증 + 함수 검증 + distance 부착
        Optimizer().optimize(statements)  # 상수 폴딩 (트리 제자리 변형)


class OptimizedFunctionExecutorUnit(OptimizedExecutorUnit, FunctionExecutorUnit):
    """정적 바인딩(O(1) 변수 조회)과 함수 실행/호출/반환 처리를 함께 지원하는 Executor.

    OptimizedExecutorUnit은 Variable/Assign만, FunctionExecutorUnit은
    FunctionStmt/ReturnStmt/Call만 가로채고 나머지는 전부 super()로 위임하는
    협력적 패턴이라 다중 상속으로 그대로 합쳐진다.
    """


def create_optimized_interpreter() -> Interpreter:
    """함수 + 클래스 + 정적 배열 + import + 실행 전 최적화(정적 바인딩, 상수 폴딩)가
    모두 적용된 Interpreter."""
    return Interpreter(
        assembler=FunctionAssembler(),
        checker=OptimizingChecker(),
        executor=OptimizedFunctionExecutorUnit(),
    )
