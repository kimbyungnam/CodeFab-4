import sys
from collections.abc import Callable, Iterable

from codefab.error import ParseError
from codefab.interpreter import Interpreter
from codefab.tokenizer import Tokenizer
from codefab.tokens import TokenType

EXIT_COMMANDS = {"exit", "quit"}
_UNTERMINATED_STRING_MESSAGE = "문자열이 닫히지 않았습니다."
_OPENERS = (TokenType.LEFT_BRACE, TokenType.LEFT_PAREN, TokenType.LEFT_BRACKET)
_CLOSERS = (TokenType.RIGHT_BRACE, TokenType.RIGHT_PAREN, TokenType.RIGHT_BRACKET)


class Repl:
    def __init__(
        self,
        interpreter: Interpreter,
        output: Callable[[str], None] | None = None,
        prompt: str = "> ",
        continuation_prompt: str = "... ",
    ):
        self._interpreter = interpreter
        self._output = output if output is not None else print
        self._prompt = prompt
        self._continuation_prompt = continuation_prompt

    def run(self, input_lines: Iterable[str]) -> None:
        iterator = iter(input_lines)
        buffer: list[str] = []
        while True:
            self._show_prompt(self._continuation_prompt if buffer else self._prompt)
            try:
                line = next(iterator)
            except StopIteration:
                # 아직 안 닫힌 입력이 남아있는데 EOF가 오면, 버리지 않고 마지막으로
                # 한 번 실행을 시도해서 (닫는 괄호 누락 같은) 실제 에러를 보여준다.
                if buffer:
                    self.run_source("\n".join(buffer))
                break
            if not buffer and line.strip() in EXIT_COMMANDS:
                break

            buffer.append(line)
            source = "\n".join(buffer)
            if self._is_incomplete(source):
                continue

            self.run_source(source)
            buffer = []

    def _is_incomplete(self, source: str) -> bool:
        # { }, ( ) 가 아직 안 닫혔거나 문자열이 안 끝났으면(여러 줄에 걸쳐 있으면)
        # 계속 다음 줄까지 입력을 이어받는다.
        try:
            tokens = Tokenizer(source).scan_tokens()
        except ParseError as exc:
            return _UNTERMINATED_STRING_MESSAGE in str(exc)
        except Exception:  # noqa: BLE001 — 그 외 토큰화 실패는 그대로 실행해서 에러를 보여준다
            return False

        depth = 0
        for token in tokens:
            if token.type in _OPENERS:
                depth += 1
            elif token.type in _CLOSERS:
                depth -= 1
        return depth > 0

    def _show_prompt(self, prompt: str) -> None:
        # 기본 출력(print)일 때는 줄바꿈 없이 찍어서 입력이 프롬프트와 같은 줄에 오게 한다.
        # 커스텀 output 콜백이 주어진 경우(테스트 등)는 기존처럼 그대로 전달한다.
        if self._output is print:
            print(prompt, end="", flush=True)
        else:
            self._output(prompt)

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
