from codefab.assembler.function_assembler import FunctionAssembler
from codefab.checker import FunctionChecker
from codefab.executor import FunctionExecutorUnit
from codefab.pipeline.interpreter import Interpreter


def create_function_interpreter() -> Interpreter:
    """함수 선언/호출/반환을 지원하는 파이프라인으로 구성된 Interpreter를 만든다.

    Assembler/Checker/Executor 각각에 함수 지원을 얹은 서브클래스
    (FunctionAssembler / FunctionChecker / FunctionExecutorUnit)를 조립하기만
    하면 되고, 기존 Interpreter/Assembler/Checker/ExecutorUnit 코드는 변경하지
    않는다.
    """
    return Interpreter(
        assembler=FunctionAssembler(),
        checker=FunctionChecker(),
        executor=FunctionExecutorUnit(),
    )
