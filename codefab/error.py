"""CodeFab 파이프라인에서 발생 가능한 모든 에러를 정의하는 단일 모듈.

에러 하나당 클래스 하나씩 대응하며, 각 클래스의 고정 메시지가 곧 실제로 사용자에게
보여지는 에러 메시지다. 새로운 에러 메시지가 필요하면 이 모듈에 클래스를 추가한다.
"""


class CodeFabError(Exception):
    """Assembler/Checker/Executor 전 단계에서 공통으로 사용하는 에러 기반 클래스."""

    def __init__(self, message: str, line: int | None = None):
        self.message = message
        self.line = line
        if line is not None:
            message = f"[{line}번째 줄] {message}"
        super().__init__(message)


class ParseError(CodeFabError):
    """Assembler Unit(파싱 단계)에서 문법 규칙을 어겼을 때 발생하는 오류의 기반 클래스."""


class CheckerError(CodeFabError):
    """Checker Unit의 정적 검사 규칙을 어겼을 때 발생하는 오류의 기반 클래스."""


class ExecutorRuntimeError(CodeFabError):
    """Executor Unit에서 실행 중 발생하는 런타임 오류의 기반 클래스."""

    def __init__(self, message: str, line: int = 1):
        super().__init__(message, line)


# ---------------- Checker Unit ----------------


class DuplicateVariableError(CheckerError):
    def __init__(self, line: int | None = None):
        super().__init__("이미 선언된 변수입니다.", line)


class SelfReferenceInInitializerError(CheckerError):
    def __init__(self, line: int | None = None):
        super().__init__("지역 변수 자기 참조 에러입니다.", line)


# ---------------- Executor Unit ----------------


class UndefinedVariableError(ExecutorRuntimeError):
    def __init__(self, name: str, line: int = 1):
        super().__init__(f"정의되지 않은 변수 '{name}'입니다.", line)


class UnsupportedStatementError(ExecutorRuntimeError):
    def __init__(self, node_type: str, line: int = 1):
        super().__init__(f"지원하지 않는 Statement입니다: '{node_type}'", line)


class UnsupportedExpressionError(ExecutorRuntimeError):
    def __init__(self, node_type: str, line: int = 1):
        super().__init__(f"지원하지 않는 Expression입니다: '{node_type}'", line)


class InvalidOperandTypeError(ExecutorRuntimeError):
    def __init__(self, line: int = 1):
        super().__init__("피연산자는 반드시 숫자여야 합니다.", line)


class UnsupportedUnaryOperatorError(ExecutorRuntimeError):
    def __init__(self, lexeme: str, line: int = 1):
        super().__init__(f"지원하지 않는 단항 연산자입니다: '{lexeme}'", line)


class UnsupportedBinaryOperatorError(ExecutorRuntimeError):
    def __init__(self, lexeme: str, line: int = 1):
        super().__init__(f"지원하지 않는 이항 연산자입니다: '{lexeme}'", line)


class DivisionByZeroError(ExecutorRuntimeError):
    def __init__(self, line: int = 1):
        super().__init__("0으로 나눈 오류입니다.", line)


class MismatchedPlusOperandTypeError(ExecutorRuntimeError):
    def __init__(self, line: int = 1):
        super().__init__("피연산자는 둘 다 숫자이거나 둘 다 문자열이어야 합니다.", line)


# ---------------- Assembler Unit ----------------


class InvalidAssignmentTargetError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("잘못된 대입 대상입니다.", line)


class UnrecognizedExpressionError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("아직 처리하지 않는 표현식 종류입니다.", line)


class MissingClosingParenAfterExpressionError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("표현식 뒤에는 ')'가 필요합니다.", line)


class MissingSemicolonAfterValueError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("값 뒤에는 ';'가 필요합니다.", line)


class MissingClosingBraceError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("블록은 '}'로 닫아야 합니다.", line)


class MissingLeftParenAfterForError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("'반복' 뒤에는 '('가 필요합니다.", line)


class MissingSemicolonAfterForConditionError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("조건식 뒤에는 ';'가 필요합니다.", line)


class MissingRightParenAfterIncrementError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("증감식 뒤에는 ')'가 필요합니다.", line)


class MissingVariableNameError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("변수 이름이 필요합니다.", line)


class MissingSemicolonAfterVarDeclarationError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("변수 선언 뒤에는 ';'가 필요합니다.", line)


class MissingLeftParenAfterIfError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("'만약' 뒤에는 '('가 필요합니다.", line)


class MissingRightParenAfterIfConditionError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("조건식 뒤에는 ')'가 필요합니다.", line)


# ---------------- Checker Unit (함수 관련 추가) ----------------


class DuplicateParameterError(CheckerError):
    def __init__(self, line: int | None = None):
        super().__init__("파라미터 이름이 중복되었습니다.", line)


class ReturnOutsideFunctionError(CheckerError):
    def __init__(self, line: int | None = None):
        super().__init__("함수 외부에서는 '반환'을 사용할 수 없습니다.", line)


# ---------------- Executor Unit (함수 관련 추가) ----------------


class NotCallableError(ExecutorRuntimeError):
    def __init__(self, line: int = 1):
        super().__init__("호출 가능한 대상(함수)이 아닙니다.", line)


class ArgumentCountMismatchError(ExecutorRuntimeError):
    def __init__(self, expected: int, actual: int, line: int = 1):
        super().__init__(
            f"인자 개수가 일치하지 않습니다. (필요: {expected}개, 전달: {actual}개)",
            line,
        )


# ---------------- Assembler Unit (import 관련 추가) ----------------


class MissingImportPathError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("가져올 파일 경로는 문자열이어야 합니다.", line)


class MissingAliasKeywordError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("'별칭' 키워드가 필요합니다.", line)


class MissingAliasNameError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("별칭 이름이 필요합니다.", line)


class MissingSemicolonAfterImportError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("가져오기 문 뒤에는 ';'가 필요합니다.", line)
