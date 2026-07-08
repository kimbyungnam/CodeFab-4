from pathlib import Path

from codefab.assembler.assembler import Assembler
from codefab.ast_nodes import ImportStmt, Stmt, VarStmt
from codefab.error import ImportedFileNotFoundError, InvalidModuleContentError


class ModuleLoader:
    """가져오기(import) 대상 파일을 읽고, 선언(가져오기/변수)만 담고 있는지 검증한다.

    순환 import 검사는 아직 하지 않는다 — 순환 구조의 파일을 로드하면 재귀
    호출이 무한히 반복된다. 이는 후속 작업(circular import 검사)에서 다룬다.
    """

    def __init__(self, assembler: Assembler | None = None):
        self._assembler = assembler if assembler is not None else Assembler()

    def resolve(self, path_literal: str) -> Path:
        return (Path.cwd() / path_literal).resolve()

    def load(self, path: Path, *, referencing_line: int) -> list[Stmt]:
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            raise ImportedFileNotFoundError(str(path), referencing_line) from None

        statements = self._assembler.assemble(source)
        self._validate_declarations_only(statements, path, referencing_line)
        return statements

    def _validate_declarations_only(
        self, statements: list[Stmt], path: Path, referencing_line: int
    ):
        for stmt in statements:
            if isinstance(stmt, ImportStmt):
                nested_path = self.resolve(stmt.path.literal)
                self.load(nested_path, referencing_line=stmt.path.line)
            elif not isinstance(stmt, VarStmt):
                raise InvalidModuleContentError(str(path), referencing_line)
