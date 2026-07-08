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


def test_exit_입력시_남은_statement를_실행하지_않고_종료한다(tmp_path, capsys):
    script = tmp_path / "script.txt"
    script.write_text("출력 1;\n출력 2;\n출력 3;\n", encoding="utf-8")
    calls = []
    commands = ["step", "exit"]
    runner = DebugRunner(output=calls.append, input_source=_fake_input(commands))

    exit_code = runner.run_file(str(script))

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "1" in out
    assert "2" not in out
    assert "3" not in out


def test_quit_입력시에도_종료한다(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("출력 1;\n출력 2;\n", encoding="utf-8")
    calls = []
    runner = DebugRunner(output=calls.append, input_source=_fake_input(["quit"]))

    exit_code = runner.run_file(str(script))

    assert exit_code == 0


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
