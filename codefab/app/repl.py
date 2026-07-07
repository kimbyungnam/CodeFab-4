import sys
from collections.abc import Callable, Iterable

from codefab.interpreter import Interpreter


class Repl:
    def __init__(
        self,
        interpreter: Interpreter,
        output: Callable[[str], None] | None = None,
        prompt: str = "> ",
    ):
        self._interpreter = interpreter
        self._output = output if output is not None else print
        self._prompt = prompt

    def run(self, input_lines: Iterable[str]) -> None:
        for line in input_lines:
            self._output(self._prompt)
            self.run_source(line)

    def run_source(self, source: str) -> None:
        result = self._interpreter.interpret(source)
        for printed_line in result.output:
            self._output(printed_line)
        if result.error is not None:
            self._output(result.error)


def main() -> int:
    try:
        Repl(interpreter=Interpreter()).run(line.rstrip("\n") for line in sys.stdin)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
