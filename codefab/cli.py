import argparse
import sys
from collections.abc import Callable

from codefab.app.debug import DebugRunner
from codefab.app.repl import main as repl_main
from codefab.interpreter import Interpreter, InterpretResult
from codefab.optimized_interpreter import create_optimized_interpreter

DEFAULT_ENCODING = "utf-8"


class FileRunner:
    def __init__(
        self,
        interpreter: Interpreter | None = None,
        output: Callable[[str], None] | None = None,
    ):
        self._interpreter = (
            interpreter if interpreter is not None else create_optimized_interpreter()
        )
        self._output = output if output is not None else print

    def run_file(self, path: str) -> int:
        try:
            with open(path, encoding=DEFAULT_ENCODING) as f:
                source = f.read()
        except OSError:
            self._output(f"파일 오류: '{path}' 파일을 찾을 수 없거나 열 수 없습니다.")
            return 1

        return self._emit(self._interpreter.interpret(source))

    def _emit(self, result: InterpretResult) -> int:
        for line in result.output:
            self._output(line)
        if result.error is not None:
            self._output(result.error)
            return 1
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="codefab")
    subparsers = parser.add_subparsers(dest="mode")

    run_parser = subparsers.add_parser(
        "run", help="파일 모드: 스크립트 파일을 실행합니다."
    )
    run_parser.add_argument("path", help="실행할 스크립트 파일 경로")

    debug_parser = subparsers.add_parser(
        "debug", help="디버그 모드: 스크립트 파일을 Stmt 단위로 실행합니다."
    )
    debug_parser.add_argument("path", help="디버그할 스크립트 파일 경로")

    args = parser.parse_args(argv)

    if args.mode == "run":
        return FileRunner().run_file(args.path)

    if args.mode == "debug":
        return DebugRunner().run_file(args.path)

    return repl_main()


if __name__ == "__main__":
    sys.exit(main())
