import contextlib
import io
from collections.abc import Callable, Iterable

from codefab.assembler.assembler import Assembler, StatementParser
from codefab.assembler.errors import ParseError
from codefab.checker import Checker
from codefab.executor_unit import ExecutorRuntimeError, ExecutorUnit
from codefab.tokenizer import Tokenizer
from codefab.tokens import Token


class Repl:
    def __init__(
        self,
        create_statement_parser: Callable[[list[Token]], StatementParser],
        tokenize: Callable[[str], list[Token]] | None = None,
        checker: Checker | None = None,
        executor: ExecutorUnit | None = None,
        output: Callable[[str], None] | None = None,
        prompt: str = "> ",
    ):
        self._create_statement_parser = create_statement_parser
        self._tokenize = tokenize if tokenize is not None else self._default_tokenize
        self._checker = checker if checker is not None else Checker()
        self._executor = executor if executor is not None else ExecutorUnit()
        self._output = output if output is not None else print
        self._prompt = prompt

    @staticmethod
    def _default_tokenize(source: str) -> list[Token]:
        return Tokenizer(source).scan_tokens()

    def run(self, input_lines: Iterable[str]) -> None:
        for line in input_lines:
            self._output(self._prompt)
            self.run_source(line)

    def run_source(self, source: str) -> None:
        buffer = io.StringIO()
        error_message = None
        try:
            tokens = self._tokenize(source)
            statement_parser = self._create_statement_parser(tokens)
            statements = Assembler(statement_parser).assemble()
            self._checker.resolve(statements)
            with contextlib.redirect_stdout(buffer):
                self._executor.execute(statements)
        except Exception as exc:  # noqa: BLE001 — 파이프라인 각 단계의 예외 타입이 제각각이라 루프를 지키기 위해 광범위하게 잡음
            error_message = self._format_error(exc)

        for printed_line in buffer.getvalue().splitlines():
            self._output(printed_line)
        if error_message is not None:
            self._output(error_message)

    def _format_error(self, exc: Exception) -> str:
        if isinstance(exc, ParseError):
            return f"구문 오류: {exc}"
        if isinstance(exc, ExecutorRuntimeError):
            return f"실행 오류 (줄 {exc.line}): {exc.message}"
        if isinstance(exc, ValueError):
            return f"검사 오류: {exc}"
        return str(exc)
