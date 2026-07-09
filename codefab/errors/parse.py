from codefab.errors.base import CodeFabError


class ParseError(CodeFabError):
    """Assembler Unit(파싱 단계)에서 문법 규칙을 어겼을 때 발생하는 오류의 기반 클래스."""


class UnexpectedEndOfInputError(ParseError):
    """토큰이 모자라서(EOF) 파싱을 못 끝낸 경우. 어떻게든 못 고치는 진짜 문법
    오류(ParseError)와 달리, 입력이 더 오면 해결될 수 있는 상태를 가리킨다
    (REPL이 이 예외만 보고 "다음 줄까지 기다릴지"를 판단한다)."""


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


class MissingRightBracketAfterIndexError(ParseError):
    def __init__(self, line: int | None = None):
        super().__init__("인덱스 뒤에는 ']'가 필요합니다.", line)


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
