import sys
from collections.abc import Callable, Iterable

from codefab.assembler.assembler import Assembler
from codefab.ast_nodes import IfStmt
from codefab.error import UnexpectedEndOfInputError
from codefab.function_interpreter import create_function_interpreter
from codefab.interpreter import Interpreter
from codefab.tokenizer import Tokenizer
from codefab.tokens import TokenType

EXIT_COMMANDS = {"exit", "quit"}
ELSE_KEYWORDS = {"아니면", "else"}
_BODY_LEADING_KEYWORDS = (TokenType.IF, TokenType.FOR)
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
        awaiting_else = False
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

            if line.strip() in EXIT_COMMANDS:
                # 여러 줄을 이어받는 중이었어도(아직 안 닫힌 괄호, 아니면 대기 등)
                # exit/quit이 나오면 그 버퍼는 버리고 바로 종료한다.
                break

            if awaiting_else:
                awaiting_else = False
                if self._starts_with_else(line):
                    buffer.append(line)
                    source = "\n".join(buffer)
                    if self._is_incomplete(source):
                        continue
                    self.run_source(source)
                    buffer = []
                    continue
                # 아니면이 안 왔으니, 보류해뒀던 (아니면 없는) 만약을 먼저 실행하고
                # 이번에 읽은 줄은 새 명령으로 이어서 처리한다.
                self.run_source("\n".join(buffer))
                buffer = []

            buffer.append(line)
            source = "\n".join(buffer)
            if self._is_incomplete(source):
                continue

            if self._is_bare_if_without_else(source):
                # `}`까지는 완전한 문장이지만, 다음 줄에 '아니면'이 붙을 수도 있으니
                # 한 줄 더 보고 확정한다.
                awaiting_else = True
                continue

            self.run_source(source)
            buffer = []

    def _starts_with_else(self, line: str) -> bool:
        stripped = line.strip()
        first_word = stripped.split(maxsplit=1)[0] if stripped else ""
        return first_word in ELSE_KEYWORDS

    def _is_incomplete(self, source: str) -> bool:
        # { }, ( ), [ ] 가 안 닫혔거나 문자열이 안 끝났으면(어떤 문장이든 공통으로
        # 애매함 없이 미완성이 확정) 다음 줄까지 기다린다.
        try:
            tokens = Tokenizer(source).scan_tokens()
        except UnexpectedEndOfInputError:
            return True
        except Exception:  # noqa: BLE001 — 그 외 토큰화 실패는 그대로 실행해서 에러를 보여준다
            return False

        if self._bracket_depth(tokens) > 0:
            return True

        # 세미콜론/대입값 누락처럼 "그냥 안 쓴 것"과 구분이 안 되는 경우는 기다리지
        # 않는다. 다만 '만약'/'반복'은 조건까지만 쓰고 몸통이 아예 없을 수 있어서
        # (중괄호 없는 형태), 이 경우만 실제로 파싱해봐서 확인한다.
        if tokens and tokens[0].type in _BODY_LEADING_KEYWORDS:
            try:
                Assembler().assemble(source)
            except UnexpectedEndOfInputError:
                return True
            except Exception:  # noqa: BLE001
                return False

        return False

    def _bracket_depth(self, tokens: list) -> int:
        depth = 0
        for token in tokens:
            if token.type in _OPENERS:
                depth += 1
            elif token.type in _CLOSERS:
                depth -= 1
        return depth

    def _is_bare_if_without_else(self, source: str) -> bool:
        try:
            statements = Assembler().assemble(source)
        except Exception:  # noqa: BLE001
            return False
        return (
            len(statements) == 1
            and isinstance(statements[0], IfStmt)
            and statements[0].else_branch is None
        )

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
        Repl(interpreter=create_function_interpreter()).run(
            line.rstrip("\n") for line in sys.stdin
        )
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
