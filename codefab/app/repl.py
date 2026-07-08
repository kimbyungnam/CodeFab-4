import sys
from collections.abc import Callable, Iterable

from codefab.interpreter import Interpreter

EXIT_COMMANDS = {"exit", "quit"}


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
        iterator = iter(input_lines)
        while True:
            self._show_prompt()
            try:
                line = next(iterator)
            except StopIteration:
                break
            if line.strip() in EXIT_COMMANDS:
                break
            self.run_source(line)

    def _show_prompt(self) -> None:
        # 기본 출력(print)일 때는 줄바꿈 없이 찍어서 입력이 프롬프트와 같은 줄에 오게 한다.
        # 커스텀 output 콜백이 주어진 경우(테스트 등)는 기존처럼 그대로 전달한다.
        if self._output is print:
            print(self._prompt, end="", flush=True)
        else:
            self._output(self._prompt)

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
