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


class UnexpectedEndOfInputError(ParseError):
    """토큰이 모자라서(EOF) 파싱을 못 끝낸 경우. 어떻게든 못 고치는 진짜 문법
    오류(ParseError)와 달리, 입력이 더 오면 해결될 수 있는 상태를 가리킨다
    (REPL이 이 예외만 보고 "다음 줄까지 기다릴지"를 판단한다)."""


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


class ThisOutsideClassError(CheckerError):
    def __init__(self, line: int | None = None):
        super().__init__("클래스 외부에서는 '나'를 사용할 수 없습니다.", line)


class SuperOutsideClassError(CheckerError):
    def __init__(self, line: int | None = None):
        super().__init__("클래스 외부에서는 '부모'를 사용할 수 없습니다.", line)


class SuperWithoutSuperclassError(CheckerError):
    def __init__(self, line: int | None = None):
        super().__init__(
            "부모 클래스가 없는 클래스 내부에서는 '부모'를 사용할 수 없습니다.", line
        )


class SelfInheritanceError(CheckerError):
    def __init__(self, line: int | None = None):
        super().__init__("클래스는 자기 자신을 상속할 수 없습니다.", line)


class ReturnInInitializerError(CheckerError):
    def __init__(self, line: int | None = None):
        super().__init__("생성자에서는 '반환'을 사용할 수 없습니다.", line)


class ImportInsideLoopError(CheckerError):
    def __init__(self, line: int | None = None):
        super().__init__("반복문 내부에서는 가져오기를 사용할 수 없습니다.", line)


class ImportedFileNotFoundError(CheckerError):
    def __init__(self, path: str, line: int | None = None):
        super().__init__(f"가져올 파일을 찾을 수 없습니다: '{path}'", line)


class InvalidModuleContentError(CheckerError):
    def __init__(self, path: str, line: int | None = None):
        super().__init__(
            f"가져온 파일 '{path}'에는 가져오기, 변수 선언만 작성할 수 있습니다.", line
        )


class CircularImportError(CheckerError):
    def __init__(self, path: str, line: int | None = None):
        super().__init__(f"순환 import가 발생했습니다: '{path}'", line)


class DuplicateImportError(CheckerError):
    def __init__(self, path: str, line: int | None = None):
        super().__init__(f"이미 가져온 파일입니다: '{path}'", line)


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


class MissingClassNameAfterInstanceOfError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("'타입확인' 뒤에는 클래스 이름이 필요합니다.", line)


class MissingPropertyNameAfterDotError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("'.' 뒤에는 속성 이름이 필요합니다.", line)


class MissingRightParenAfterArgumentsError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("인자 목록 뒤에는 ')'가 필요합니다.", line)


class MissingDotAfterSuperError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("'부모' 뒤에는 '.'이 필요합니다.", line)


class MissingMethodNameAfterSuperError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("'부모.' 뒤에는 메서드 이름이 필요합니다.", line)


class MissingLeftParenAfterArrayError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("'배열' 뒤에는 '('가 필요합니다.", line)


class MissingSemicolonAfterReturnError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("반환 값 뒤에는 ';'가 필요합니다.", line)


class MissingClassNameError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("클래스 이름이 필요합니다.", line)


class MissingSuperclassNameError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("상속할 클래스 이름이 필요합니다.", line)


class MissingLeftBraceForClassBodyError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("클래스 본문은 '{'로 시작해야 합니다.", line)


class MissingRightBraceForClassBodyError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("클래스 본문은 '}'로 닫아야 합니다.", line)


class MissingMethodNameError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("메서드 이름이 필요합니다.", line)


class MissingLeftParenAfterMethodNameError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("메서드 이름 뒤에는 '('가 필요합니다.", line)


class MissingParameterNameError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("매개변수 이름이 필요합니다.", line)


class MissingRightParenAfterParameterListError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("매개변수 목록 뒤에는 ')'가 필요합니다.", line)


class MissingLeftBraceForMethodBodyError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("메서드 본문은 '{'로 시작해야 합니다.", line)


# ---------------- Assembler Unit (함수 관련 추가) ----------------


class MissingFunctionNameError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("함수 이름이 필요합니다.", line)


class MissingLeftParenAfterFunctionNameError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("함수 이름 뒤에는 '('가 필요합니다.", line)


class MissingFunctionParameterNameError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("파라미터 이름이 필요합니다.", line)


class MissingRightParenAfterFunctionParameterListError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("파라미터 목록 뒤에는 ')'가 필요합니다.", line)


class MissingLeftBraceForFunctionBodyError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("함수 본문은 '{'로 시작해야 합니다.", line)


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


class MissingRightBracketAfterIndexError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("인덱스 뒤에는 ']'가 필요합니다.", line)


# ---------------- 정적 배열 (Executor Unit) ----------------


class ArraySizeNotNumberError(ExecutorRuntimeError):
    def __init__(self, line: int = 1):
        super().__init__("배열의 크기는 반드시 숫자여야 합니다.", line)


class ArrayIndexNotNumberError(ExecutorRuntimeError):
    def __init__(self, line: int = 1):
        super().__init__("배열의 인덱스는 반드시 숫자여야 합니다.", line)


class ArrayIndexOutOfRangeError(ExecutorRuntimeError):
    def __init__(self, line: int = 1):
        super().__init__("배열의 인덱스 범위를 벗어났습니다.", line)


class NotIndexableError(ExecutorRuntimeError):
    def __init__(self, node_type: str, line: int = 1):
        super().__init__(
            f"'[]' 연산은 배열에만 사용할 수 있습니다: '{node_type}'", line
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


# ---------------- Executor Unit (import 관련 추가) ----------------


class UndefinedModuleMemberError(ExecutorRuntimeError):
    def __init__(self, name: str, line: int = 1):
        super().__init__(f"정의되지 않은 멤버 '{name}'입니다.", line)
