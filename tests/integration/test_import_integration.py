"""가져오기(import) 기능의 Assembler -> Checker -> Executor 전체 파이프라인 통합 테스트.

ModuleLoader가 실제 파일 시스템을 사용하므로 tmp_path를 현재 작업 디렉터리로
설정해 상대 경로 해석을 검증한다.
"""

from codefab.pipeline import Interpreter


def test_가져온_모듈의_변수를_점_표기로_읽고_출력한다(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "math.txt").write_text("변수 pi = 3.14;", encoding="utf-8")

    result = Interpreter().interpret('가져오기 "math.txt" 별칭 math;\n출력 math.pi;')

    assert result.error is None
    assert result.output == ["3.14"]


def test_중첩된_가져오기가_있는_모듈도_정상_실행된다(tmp_path, monkeypatch):
    # math.txt 자신이 base.txt 를 가져오더라도, math 모듈 실행 자체는 문제없이 끝나야 한다.
    monkeypatch.chdir(tmp_path)
    (tmp_path / "base.txt").write_text("변수 e = 2.72;", encoding="utf-8")
    (tmp_path / "math.txt").write_text(
        '가져오기 "base.txt" 별칭 base;\n변수 pi = 3.14;', encoding="utf-8"
    )

    result = Interpreter().interpret('가져오기 "math.txt" 별칭 math;\n출력 math.pi;')

    assert result.error is None
    assert result.output == ["3.14"]


def test_존재하지_않는_파일을_가져오면_실행_전에_에러로_중단된다(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    result = Interpreter().interpret('가져오기 "missing.txt" 별칭 m;\n출력 1;')

    assert result.output == []
    assert "찾을 수 없습니다" in result.error


def test_모듈에_없는_멤버를_읽으면_런타임_에러가_발생한다(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "math.txt").write_text("변수 pi = 3.14;", encoding="utf-8")

    result = Interpreter().interpret(
        '가져오기 "math.txt" 별칭 math;\n출력 math.notExist;'
    )

    assert result.output == []
    assert "정의되지 않은 멤버" in result.error
