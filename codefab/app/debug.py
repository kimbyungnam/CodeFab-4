from collections.abc import Callable

DEFAULT_ENCODING = "utf-8"


class DebugRunner:
    def __init__(self, output: Callable[[str], None] | None = None):
        self._output = output if output is not None else print

    def run_file(self, path: str) -> int:
        try:
            with open(path, encoding=DEFAULT_ENCODING) as f:
                f.read()
        except OSError:
            self._output(f"파일 오류: '{path}' 파일을 찾을 수 없거나 열 수 없습니다.")
            return 1

        self._output(f"[DEBUG] 소스코드 로딩 : {path}")
        return 0
