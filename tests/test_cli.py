import pytest

from codefab.cli import Cli, main
from codefab.interpreter import Interpreter, InterpretResult


def test_파일을_읽어_interpreter에_source로_전달한다(mocker, tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("변수 a = 3; 출력 a;", encoding="utf-8")
    interpreter = mocker.Mock(spec=Interpreter)
    interpreter.interpret.return_value = InterpretResult()
    cli = Cli(interpreter=interpreter, output=mocker.Mock())

    cli.run_file(str(script))

    interpreter.interpret.assert_called_once_with("변수 a = 3; 출력 a;")


def test_output_라인이_순서대로_output_콜백에_전달된다(mocker, tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("아무거나", encoding="utf-8")
    interpreter = mocker.Mock(spec=Interpreter)
    interpreter.interpret.return_value = InterpretResult(output=["1", "2"])
    calls = []
    cli = Cli(interpreter=interpreter, output=calls.append)

    exit_code = cli.run_file(str(script))

    assert calls == ["1", "2"]
    assert exit_code == 0


def test_error가_있으면_error_메시지도_출력되고_종료코드가_1이다(mocker, tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("아무거나", encoding="utf-8")
    interpreter = mocker.Mock(spec=Interpreter)
    interpreter.interpret.return_value = InterpretResult(
        output=["1"], error="실행 오류 (줄 3): 0으로 나눈 오류"
    )
    calls = []
    cli = Cli(interpreter=interpreter, output=calls.append)

    exit_code = cli.run_file(str(script))

    assert calls == ["1", "실행 오류 (줄 3): 0으로 나눈 오류"]
    assert exit_code == 1


def test_error가_없으면_종료코드가_0이다(mocker, tmp_path):
    script = tmp_path / "script.txt"
    script.write_text("아무거나", encoding="utf-8")
    interpreter = mocker.Mock(spec=Interpreter)
    interpreter.interpret.return_value = InterpretResult(output=[], error=None)
    cli = Cli(interpreter=interpreter, output=mocker.Mock())

    exit_code = cli.run_file(str(script))

    assert exit_code == 0


def test_존재하지_않는_파일이면_파일_오류_메시지를_출력하고_1을_반환한다(
    mocker, tmp_path
):
    missing = tmp_path / "없는파일.txt"
    interpreter = mocker.Mock(spec=Interpreter)
    calls = []
    cli = Cli(interpreter=interpreter, output=calls.append)

    exit_code = cli.run_file(str(missing))

    assert len(calls) == 1
    assert "파일 오류" in calls[0]
    interpreter.interpret.assert_not_called()
    assert exit_code == 1


def test_utf8_한글_스크립트_파일을_정상적으로_실행한다(mocker, tmp_path):
    from codefab.checker import Checker

    script = tmp_path / "script.txt"
    script.write_text("변수 a = 3; 출력 a;", encoding="utf-8")
    calls = []
    cli = Cli(
        interpreter=Interpreter(checker=mocker.Mock(spec=Checker)), output=calls.append
    )

    exit_code = cli.run_file(str(script))

    assert calls == ["3"]
    assert exit_code == 0


def test_main이_run_경로_인자를_cli_run_file에_전달한다(mocker):
    run_file = mocker.patch.object(Cli, "run_file", return_value=0)

    exit_code = main(["run", "script.txt"])

    run_file.assert_called_once_with("script.txt")
    assert exit_code == 0


def test_run_서브커맨드에_경로_인자가_없으면_SystemExit이_발생한다():
    with pytest.raises(SystemExit):
        main(["run"])


def test_main에_인자가_없으면_repl_모드로_진입한다(mocker):
    repl_main = mocker.patch("codefab.cli.repl_main", return_value=0)

    exit_code = main([])

    repl_main.assert_called_once_with()
    assert exit_code == 0
