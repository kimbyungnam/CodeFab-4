class CodeFabError(Exception):
    """Assembler/Checker/Executor 전 단계에서 공통으로 사용하는 에러 기반 클래스."""

    def __init__(self, message: str, line: int | None = None):
        self.message = message
        self.line = line
        if line is not None:
            message = f"[{line}번째 줄] {message}"
        super().__init__(message)
