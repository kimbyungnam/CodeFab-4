import pytest

from codefab.ast import ImportStmt, VarStmt
from codefab.common.module_loader import ModuleLoader
from codefab.errors import (
    CircularImportError,
    ImportedFileNotFoundError,
    InvalidModuleContentError,
)


@pytest.fixture
def loader():
    return ModuleLoader()


def test_resolve는_현재_작업_디렉터리_기준으로_경로를_해석한다(
    loader, tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)

    resolved = loader.resolve("sum.txt")

    assert resolved == (tmp_path / "sum.txt").resolve()


def test_load는_변수_선언만_있는_파일을_읽어_파싱한다(loader, tmp_path):
    file_path = tmp_path / "sum.txt"
    file_path.write_text("변수 x = 3;", encoding="utf-8")

    statements = loader.load(file_path, referencing_line=1)

    assert len(statements) == 1
    assert isinstance(statements[0], VarStmt)


def test_load는_중첩된_가져오기를_재귀적으로_검증한다(loader, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.txt").write_text("변수 x = 1;", encoding="utf-8")
    (tmp_path / "b.txt").write_text(
        '가져오기 "a.txt" 별칭 a;\n변수 y = 2;', encoding="utf-8"
    )

    statements = loader.load(tmp_path / "b.txt", referencing_line=1)

    assert len(statements) == 2
    assert isinstance(statements[0], ImportStmt)
    assert isinstance(statements[1], VarStmt)


def test_존재하지_않는_파일을_가져오면_에러(loader, tmp_path):
    missing_path = tmp_path / "missing.txt"

    with pytest.raises(ImportedFileNotFoundError):
        loader.load(missing_path, referencing_line=3)


def test_선언이_아닌_구문이_있으면_에러(loader, tmp_path):
    file_path = tmp_path / "bad.txt"
    file_path.write_text("출력 1;", encoding="utf-8")

    with pytest.raises(InvalidModuleContentError):
        loader.load(file_path, referencing_line=1)


def test_중첩된_파일의_선언_외_구문도_에러로_전파된다(loader, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "bad_nested.txt").write_text("출력 1;", encoding="utf-8")
    (tmp_path / "main.txt").write_text(
        '가져오기 "bad_nested.txt" 별칭 bad;', encoding="utf-8"
    )

    with pytest.raises(InvalidModuleContentError):
        loader.load(tmp_path / "main.txt", referencing_line=1)


def test_자기_자신을_가져오면_순환_import_에러(loader, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.txt").write_text('가져오기 "a.txt" 별칭 a;', encoding="utf-8")

    with pytest.raises(CircularImportError):
        loader.load(tmp_path / "a.txt", referencing_line=1)


def test_서로를_가져오면_순환_import_에러(loader, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.txt").write_text('가져오기 "b.txt" 별칭 b;', encoding="utf-8")
    (tmp_path / "b.txt").write_text('가져오기 "a.txt" 별칭 a;', encoding="utf-8")

    with pytest.raises(CircularImportError):
        loader.load(tmp_path / "a.txt", referencing_line=1)


def test_세_파일이_간접적으로_순환_참조하면_순환_import_에러(
    loader, tmp_path, monkeypatch
):
    # a.txt -> b.txt -> c.txt -> a.txt (직접 서로를 가져오지는 않지만 간접 순환)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "a.txt").write_text('가져오기 "b.txt" 별칭 b;', encoding="utf-8")
    (tmp_path / "b.txt").write_text('가져오기 "c.txt" 별칭 c;', encoding="utf-8")
    (tmp_path / "c.txt").write_text('가져오기 "a.txt" 별칭 a;', encoding="utf-8")

    with pytest.raises(CircularImportError):
        loader.load(tmp_path / "a.txt", referencing_line=1)


def test_순환이_아닌_다이아몬드_형태의_import는_허용한다(loader, tmp_path, monkeypatch):
    # a.txt -> b.txt, c.txt 둘 다 -> shared.txt (순환은 아님)
    monkeypatch.chdir(tmp_path)
    (tmp_path / "shared.txt").write_text("변수 x = 1;", encoding="utf-8")
    (tmp_path / "b.txt").write_text('가져오기 "shared.txt" 별칭 s;', encoding="utf-8")
    (tmp_path / "c.txt").write_text('가져오기 "shared.txt" 별칭 s;', encoding="utf-8")
    (tmp_path / "a.txt").write_text(
        '가져오기 "b.txt" 별칭 b;\n가져오기 "c.txt" 별칭 c;', encoding="utf-8"
    )

    statements = loader.load(tmp_path / "a.txt", referencing_line=1)

    assert len(statements) == 2
