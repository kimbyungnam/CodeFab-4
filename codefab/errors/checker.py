from codefab.errors.base import CodeFabError


class CheckerError(CodeFabError):
    """Checker Unit의 정적 검사 규칙을 어겼을 때 발생하는 오류의 기반 클래스."""


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


# ---------------- Checker Unit (함수 관련 추가) ----------------


class DuplicateParameterError(CheckerError):
    def __init__(self, line: int | None = None):
        super().__init__("파라미터 이름이 중복되었습니다.", line)


class ReturnOutsideFunctionError(CheckerError):
    def __init__(self, line: int | None = None):
        super().__init__("함수 외부에서는 '반환'을 사용할 수 없습니다.", line)
