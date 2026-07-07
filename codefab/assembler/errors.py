class ParseError(Exception):
    """Expression 파싱 중 문법 규칙을 어겼을 때 발생하는 오류."""

    def __init__(self, message: str, line: int | None = None) -> None:
        self.line = line
        if line is not None:
            message = f"[{line}번째 줄] {message}"
        super().__init__(message)
