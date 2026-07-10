from codefab.errors.base import CodeFabError


class ExecutorRuntimeError(CodeFabError):
    """Executor Unit에서 실행 중 발생하는 런타임 오류의 기반 클래스."""

    def __init__(self, message: str, line: int = 1):
        super().__init__(message, line)


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


class OnlyInstancesHaveFieldsError(ExecutorRuntimeError):
    def __init__(self, line: int = 1):
        super().__init__("인스턴스만 필드를 가질 수 있습니다.", line)


class UndefinedPropertyError(ExecutorRuntimeError):
    def __init__(self, name: str, line: int = 1):
        super().__init__(f"정의되지 않은 필드/메서드 '{name}'입니다.", line)


class SuperclassMustBeClassError(ExecutorRuntimeError):
    def __init__(self, line: int = 1):
        super().__init__("클래스가 아닌 대상은 상속할 수 없습니다.", line)


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


# ---------------- 정적 배열 (Executor Unit) ----------------


class ArraySizeNotNumberError(ExecutorRuntimeError):
    def __init__(self, line: int = 1):
        super().__init__("배열의 크기는 반드시 숫자여야 합니다.", line)


class ArraySizeNegativeError(ExecutorRuntimeError):
    def __init__(self, line: int = 1):
        super().__init__("배열의 크기는 음수일 수 없습니다.", line)


class ArraySizeNotIntegerError(ExecutorRuntimeError):
    def __init__(self, line: int = 1):
        super().__init__("배열의 크기는 정수여야 합니다.", line)


class ArrayIndexNotNumberError(ExecutorRuntimeError):
    def __init__(self, line: int = 1):
        super().__init__("배열의 인덱스는 반드시 숫자여야 합니다.", line)


class ArrayIndexNotIntegerError(ExecutorRuntimeError):
    def __init__(self, line: int = 1):
        super().__init__("배열의 인덱스는 정수여야 합니다.", line)


class ArrayIndexOutOfRangeError(ExecutorRuntimeError):
    def __init__(self, line: int = 1):
        super().__init__("배열의 인덱스 범위를 벗어났습니다.", line)


class NotIndexableError(ExecutorRuntimeError):
    def __init__(self, node_type: str, line: int = 1):
        super().__init__(
            f"'[]' 연산은 배열에만 사용할 수 있습니다: '{node_type}'", line
        )


# ---------------- Executor Unit (import 관련 추가) ----------------


class UndefinedModuleMemberError(ExecutorRuntimeError):
    def __init__(self, name: str, line: int = 1):
        super().__init__(f"정의되지 않은 멤버 '{name}'입니다.", line)
