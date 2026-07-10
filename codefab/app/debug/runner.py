from collections.abc import Callable

from codefab.app.debug.debugger import DebugExitRequested, Debugger
from codefab.app.debug.formatting import line_of_stmt
from codefab.assembler.function_assembler import FunctionAssembler
from codefab.ast import BlockStmt, Stmt
from codefab.pipeline import OptimizedFunctionExecutorUnit, OptimizingChecker

DEFAULT_ENCODING = "utf-8"


class DebugExecutor(OptimizedFunctionExecutorUnit):
    def __init__(self, debugger: Debugger):
        super().__init__()
        self._debugger = debugger

    def _before_stmt(self, statement: Stmt, depth: int) -> None:
        if isinstance(statement, BlockStmt):
            return  # 블록 여는 지점 자체는 멈춤 지점이 아니고, 안쪽 statement들만 멈춘다
        self._debugger.before_stmt(line_of_stmt(statement), depth, self.environment)


class DebugRunner:
    def __init__(
        self,
        output: Callable[[str], None] | None = None,
        input_source: Callable[[], str] | None = None,
    ):
        self._output = output if output is not None else print
        self._input = input_source

    def run_file(self, path: str) -> int:
        try:
            with open(path, encoding=DEFAULT_ENCODING) as f:
                source = f.read()
        except OSError:
            self._output(f"파일 오류: '{path}' 파일을 찾을 수 없거나 열 수 없습니다.")
            return 1

        self._output(f"[DEBUG] 소스코드 로딩 : {path}")

        try:
            statements = FunctionAssembler().assemble(source)
            OptimizingChecker().resolve(statements)
        except Exception as exc:  # noqa: BLE001 — 파이프라인 각 단계의 예외 타입이 제각각이라 광범위하게 잡음
            self._output(str(exc))
            return 1

        debugger = Debugger(
            source.splitlines(), input_source=self._input, output=self._output
        )
        try:
            DebugExecutor(debugger).execute(statements)
        except DebugExitRequested:
            return 0
        except Exception as exc:  # noqa: BLE001
            self._output(str(exc))
            return 1

        return 0
