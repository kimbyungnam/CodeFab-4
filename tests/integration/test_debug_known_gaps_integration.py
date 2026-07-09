"""디버그 모드에서 `클래스` 선언 줄 번호가 정확히 보고되는지 확인하는 통합 테스트.

과거 `codefab/app/debug.py`의 `line_of_stmt()`가 `ClassStmt`/`FunctionStmt`/
`ReturnStmt`/`ImportStmt` case를 처리하지 않아 기본값 1을 반환하는 gap이 있었다
(`클래스` 선언 줄에서 멈춰야 할 때 실제 줄 번호 대신 파일의 1번째 줄 텍스트를
엉뚱하게 다시 보여줌). 지금은 해당 case들이 추가되어 고쳐졌다.
"""

import contextlib
import io

from codefab.app.debug import DebugRunner


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
