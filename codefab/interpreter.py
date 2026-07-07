import contextlib
import io
from dataclasses import dataclass, field

from codefab.assembler.assembler import Assembler
from codefab.assembler.errors import ParseError
from codefab.checker import Checker
from codefab.executor_unit import ExecutorRuntimeError, ExecutorUnit


@dataclass(frozen=True)
class InterpretResult:
    output: list[str] = field(default_factory=list)
    error: str | None = None


class Interpreter:
    def __init__(
        self,
        assembler: Assembler | None = None,
        checker: Checker | None = None,
        executor: ExecutorUnit | None = None,
    ):
        self._assembler = assembler if assembler is not None else Assembler()
        self._checker = checker if checker is not None else Checker()
        self._executor = executor if executor is not None else ExecutorUnit()

    def interpret(self, source: str) -> InterpretResult:
        buffer = io.StringIO()
        error_message = None
        try:
            statements = self._assembler.assemble(source)
            self._checker.resolve(statements)
            with contextlib.redirect_stdout(buffer):
                self._executor.execute(statements)
        except Exception as exc:  # noqa: BLE001 — 파이프라인 각 단계의 예외 타입이 제각각이라 호출자에게 전파하지 않고 광범위하게 잡음
            error_message = self._format_error(exc)

        return InterpretResult(
            output=buffer.getvalue().splitlines(), error=error_message
        )

    def _format_error(self, exc: Exception) -> str:
        if isinstance(exc, ParseError):
            return f"구문 오류: {exc}"
        # TODO: ExecutorRuntimeError도 다른 예외들처럼 str(exc)만으로 처리하고 싶지만,
        # 줄 번호(exc.line)가 메시지 문자열에 포함되어 있지 않아 별도 분기가 필요하다.
        # 예외가 스스로 줄 번호까지 포함한 문자열을 반환하게 되면 이 isinstance 분기 자체를
        # 없애고 else 분기(`return str(exc)`)로 통합할 수 있다.
        if isinstance(exc, ExecutorRuntimeError):
            return f"실행 오류 (줄 {exc.line}): {exc}"
        if isinstance(exc, ValueError):
            return f"검사 오류: {exc}"
        return str(exc)
