"""알려진 기능 격차(known gap)를 문서화하는 디버그 모드 통합 테스트.

`codefab/app/debug.py`의 `line_of_stmt()`는 `VarStmt`/`PrintStmt`/`ExpressionStmt`/
`IfStmt`/`ForStmt`만 처리하고 `ClassStmt`/`ReturnStmt` case가 없어 기본값 1을 반환한다.
그 결과 `클래스` 선언 줄에서 멈춰야 할 때 실제 줄 번호 대신 파일의 1번째 줄 텍스트를
엉뚱하게 다시 보여준다.

이 gap 때문에 `tests/integration/fixtures/laugh/normal/디버그_watch와_inspect_명령어.*`
golden fixture는 클래스를 쓰지 않는 소스만으로 작성했다 — 아래 테스트는 그 자체를
*바라는* 최종 동작(정확한 줄 번호 보고)으로 assert하고 `xfail(strict=True)`로 표시한다.
`line_of_stmt`에 `ClassStmt` case가 추가되면 XPASS로 뒤집혀 실제 golden 테스트로
교체하라는 신호가 된다.
"""

import contextlib
import io

import pytest

from codefab.app.debug import DebugRunner

_XFAIL_REASON = (
    "codefab/app/debug.py의 line_of_stmt가 ClassStmt를 처리하지 않아"
    " 클래스 선언 줄에서 멈출 때 실제 줄 번호 대신 1을 보고함"
)


@pytest.mark.xfail(strict=True, reason=_XFAIL_REASON)
def test_디버그_모드에서_클래스_선언_줄이_정확히_보고된다(tmp_path):
    script = tmp_path / "main.laugh"
    script.write_text(
        "변수 x = 1;\n"
        "클래스 Robot {\n"
        "    report() {\n"
        '        출력 "hi";\n'
        "    }\n"
        "}\n"
        "변수 r = Robot();\n"
        "r.report();\n",
        encoding="utf-8",
    )
    commands = iter(["step", "step"]).__next__

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        DebugRunner(input_source=commands).run_file(str(script))

    assert "[DEBUG] 2번째 줄에서 정지 -> 클래스 Robot {" in buffer.getvalue()
