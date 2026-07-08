import pytest

from codefab.app.debug import DebugRunner


def _fake_input(commands):
    return iter(commands).__next__


def test_존재하지_않는_파일이면_파일_오류_메시지를_출력하고_1을_반환한다(tmp_path):
    missing = tmp_path / "없는파일.txt"
    calls = []
    runner = DebugRunner(output=calls.append)

    exit_code = runner.run_file(str(missing))

    assert len(calls) == 1
    assert "파일 오류" in calls[0]
    assert exit_code == 1


@pytest.mark.parametrize("종료_명령", ["exit", "quit"])
def test_종료_명령_입력시_남은_statement를_실행하지_않고_즉시_종료한다(
    tmp_path, capsys, 종료_명령
):
    script = tmp_path / "script.txt"
    script.write_text("출력 1;\n출력 2;\n출력 3;\n", encoding="utf-8")
    calls = []
    commands = ["step", 종료_명령]
    runner = DebugRunner(output=calls.append, input_source=_fake_input(commands))

    exit_code = runner.run_file(str(script))

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "1" in out
    assert "2" not in out
    assert "3" not in out


def test_명령을_읽기_전에_프롬프트가_출력된다(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("변수 a = 3;", encoding="utf-8")
    calls = []
    runner = DebugRunner(output=calls.append, input_source=_fake_input(["step"]))

    runner.run_file(str(script))

    assert "> " in calls


def test_기본_output_사용시_프롬프트_뒤에_줄바꿈이_없다(tmp_path, capsys):
    script = tmp_path / "script.txt"
    script.write_text("변수 a = 3;", encoding="utf-8")
    runner = DebugRunner(input_source=_fake_input(["step"]))

    runner.run_file(str(script))

    out = capsys.readouterr().out
    assert (
        "> [DEBUG]" not in out
    )  # 프롬프트 자체는 줄바꿈 없이 다음 내용과 안 섞여야 함
    assert out.rstrip("\n").endswith("> ")


def test_존재하는_파일이면_소스코드_로딩_메시지를_출력한다(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("변수 a = 3;", encoding="utf-8")
    calls = []
    runner = DebugRunner(output=calls.append, input_source=_fake_input(["step"]))

    exit_code = runner.run_file(str(script))

    assert calls[0] == f"[DEBUG] 소스코드 로딩 : {script}"
    assert exit_code == 0


def test_진입하면_첫_Stmt에서_정지한다(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("변수 a = 3;\n출력 a;\n", encoding="utf-8")
    calls = []
    runner = DebugRunner(
        output=calls.append, input_source=_fake_input(["step", "step"])
    )

    runner.run_file(str(script))

    assert "[DEBUG] 1번째 줄에서 정지 -> 변수 a = 3;" in calls
    assert "[DEBUG] 2번째 줄에서 정지 -> 출력 a;" in calls


def test_step은_현재_줄을_실행하고_다음_줄에서_정지한다(tmp_path, capsys):
    script = tmp_path / "script.txt"
    script.write_text("변수 a = 3;\n출력 a;\n", encoding="utf-8")
    calls = []
    runner = DebugRunner(
        output=calls.append, input_source=_fake_input(["step", "step"])
    )

    runner.run_file(str(script))

    # 2번째 줄(출력 a;)까지 실행돼서 "3"이 (언어 자체의 출력으로) 찍힌다
    assert "3" in capsys.readouterr().out


def test_break로_설정한_줄까지_continue로_건너뛴다(tmp_path, capsys):
    script = tmp_path / "script.txt"
    script.write_text(
        "변수 a = 3;\n변수 b = a + 1;\n변수 c = 1;\n변수 d = 1;\n"
        "변수 e = 1;\n변수 f = 1;\n출력 a;\n",
        encoding="utf-8",
    )
    calls = []
    commands = ["step", "break 7", "continue", "step"]
    runner = DebugRunner(output=calls.append, input_source=_fake_input(commands))

    runner.run_file(str(script))

    assert "[DEBUG] 1번째 줄에서 정지 -> 변수 a = 3;" in calls
    assert "[DEBUG] 2번째 줄에서 정지 -> 변수 b = a + 1;" in calls
    assert "[DEBUG] 7번째 줄에 breakpoint 설정" in calls
    assert "[DEBUG] 7번째 줄에서 정지 (breakpoint) -> 출력 a;" in calls
    assert "3" in capsys.readouterr().out


def test_next는_블록_내부에서_멈추지_않고_다음_최상위_줄에서_정지한다(tmp_path, capsys):
    script = tmp_path / "script.txt"
    script.write_text(
        "변수 a = 3;\n{\n  변수 b = 10;\n  출력 b;\n}\n출력 a;\n",
        encoding="utf-8",
    )
    calls = []
    commands = ["next", "step"]
    runner = DebugRunner(output=calls.append, input_source=_fake_input(commands))

    runner.run_file(str(script))

    assert "[DEBUG] 1번째 줄에서 정지 -> 변수 a = 3;" in calls
    # 블록 내부(3, 4번째 줄)에서는 멈추지 않고 바로 6번째 줄로 건너뛴다
    assert not any("3번째 줄" in call for call in calls)
    assert not any("4번째 줄" in call for call in calls)
    assert "[DEBUG] 6번째 줄에서 정지 -> 출력 a;" in calls
    # 블록 내부는 멈추지 않았을 뿐 실제로는 실행됐으므로 "10"이 출력된다
    assert "10" in capsys.readouterr().out


def test_watch로_등록한_변수의_값이_정지할_때마다_출력된다(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("변수 a = 3;\na = a + 1;\n출력 a;\n", encoding="utf-8")
    calls = []
    commands = ["watch a", "step", "step", "step"]
    runner = DebugRunner(output=calls.append, input_source=_fake_input(commands))

    runner.run_file(str(script))

    assert "[WATCH] 'a' 감시 등록" in calls
    assert "[WATCH] a = 3" in calls
    assert "[WATCH] a = 4" in calls


def test_inspect은_로컬과_전역_변수를_타입과_함께_보여준다(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text(
        "변수 a = 3;\n{\n  변수 b = 10;\n  변수 flag = 참;\n  출력 b;\n}\n",
        encoding="utf-8",
    )
    calls = []
    commands = ["step", "step", "step", "inspect"]
    runner = DebugRunner(output=calls.append, input_source=_fake_input(commands))

    runner.run_file(str(script))

    assert "[전역] a = 3 (Number)" in calls
    assert "[로컬] b = 10 (Number)" in calls
    assert "[로컬] flag = 참 (Boolean)" in calls


def test_inspect은_문자열_변수도_타입과_함께_보여준다(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text('변수 s = "hi";\n출력 s;\n', encoding="utf-8")
    calls = []
    commands = ["step", "inspect"]
    runner = DebugRunner(output=calls.append, input_source=_fake_input(commands))

    runner.run_file(str(script))

    assert "[전역] s = hi (String)" in calls


def test_breakpoints_명령으로_설정된_breakpoint_목록을_보여준다(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("출력 1;\n출력 2;\n출력 3;\n", encoding="utf-8")
    calls = []
    commands = ["break 2", "breakpoints", "step", "step", "step"]
    runner = DebugRunner(output=calls.append, input_source=_fake_input(commands))

    runner.run_file(str(script))

    assert "[DEBUG] breakpoint: 2번째 줄" in calls


def test_remove_명령으로_breakpoint를_해제한다(tmp_path, capsys):
    script = tmp_path / "script.txt"
    script.write_text("출력 1;\n출력 2;\n출력 3;\n", encoding="utf-8")
    calls = []
    commands = ["break 2", "remove 2", "continue"]
    runner = DebugRunner(output=calls.append, input_source=_fake_input(commands))

    runner.run_file(str(script))

    assert "[DEBUG] 2번째 줄 breakpoint 해제" in calls
    # breakpoint를 해제했으므로 continue가 끝까지 실행해서 1,2,3 모두 출력된다
    out = capsys.readouterr().out
    assert "1" in out
    assert "2" in out
    assert "3" in out


def test_watches_명령으로_감시중인_변수_목록을_보여주고_unwatch로_해제한다(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("변수 a = 3;\n변수 b = 5;\n출력 a;\n", encoding="utf-8")
    calls = []
    commands = ["step", "watch a", "watches", "unwatch a", "watches", "step", "step"]
    runner = DebugRunner(output=calls.append, input_source=_fake_input(commands))

    runner.run_file(str(script))

    assert "a = 3" in calls
    assert "[WATCH] 'a' 감시 해제" in calls


def test_watch는_존재하지_않는_변수는_조용히_건너뛴다(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("출력 1;\n출력 2;\n", encoding="utf-8")
    calls = []
    commands = ["watch nope", "step", "step"]
    runner = DebugRunner(output=calls.append, input_source=_fake_input(commands))

    runner.run_file(str(script))

    assert not any(call.startswith("[WATCH] nope") for call in calls)


def test_watch는_바깥_스코프의_변수도_찾아서_보여준다(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("변수 a = 3;\n{\n  출력 a;\n}\n", encoding="utf-8")
    calls = []
    commands = ["watch a", "step", "step"]
    runner = DebugRunner(output=calls.append, input_source=_fake_input(commands))

    runner.run_file(str(script))

    assert "[WATCH] a = 3" in calls


def test_만약문에서_정지하면_조건식_줄에서_멈춘다(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text('만약 (참) 출력 "hi";\n출력 2;\n', encoding="utf-8")
    calls = []
    commands = ["step", "step", "step"]
    runner = DebugRunner(output=calls.append, input_source=_fake_input(commands))

    runner.run_file(str(script))

    assert '[DEBUG] 1번째 줄에서 정지 -> 만약 (참) 출력 "hi";' in calls


def test_반복문에서_정지하면_초기화식_줄에서_멈춘다(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text(
        "반복 (변수 i = 0; i < 2; i = i + 1) { 출력 i; }\n", encoding="utf-8"
    )
    calls = []
    commands = ["step", "exit"]
    runner = DebugRunner(output=calls.append, input_source=_fake_input(commands))

    runner.run_file(str(script))

    assert any("1번째 줄에서 정지" in call for call in calls)


def test_이항연산_출력문에서_정지하면_연산자_줄에서_멈춘다(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("변수 a = 1;\n출력 a + 1;\n", encoding="utf-8")
    calls = []
    commands = ["step", "step"]
    runner = DebugRunner(output=calls.append, input_source=_fake_input(commands))

    runner.run_file(str(script))

    assert "[DEBUG] 2번째 줄에서 정지 -> 출력 a + 1;" in calls


def test_문법_오류가_있으면_에러_메시지를_출력하고_1을_반환한다(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("출력 1 +;\n", encoding="utf-8")
    calls = []
    runner = DebugRunner(output=calls.append, input_source=_fake_input([]))

    exit_code = runner.run_file(str(script))

    assert exit_code == 1
    assert len(calls) == 2  # 로딩 메시지 + 에러 메시지
