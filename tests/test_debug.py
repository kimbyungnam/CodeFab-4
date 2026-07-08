from codefab.app.debug import DebugRunner


def test_존재하지_않는_파일이면_파일_오류_메시지를_출력하고_1을_반환한다(tmp_path):
    missing = tmp_path / "없는파일.txt"
    calls = []
    runner = DebugRunner(output=calls.append)

    exit_code = runner.run_file(str(missing))

    assert len(calls) == 1
    assert "파일 오류" in calls[0]
    assert exit_code == 1


def test_존재하는_파일이면_소스코드_로딩_메시지를_출력하고_0을_반환한다(tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("변수 a = 3;", encoding="utf-8")
    calls = []
    runner = DebugRunner(output=calls.append)

    exit_code = runner.run_file(str(script))

    assert calls == [f"[DEBUG] 소스코드 로딩 : {script}"]
    assert exit_code == 0
