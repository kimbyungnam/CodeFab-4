from codefab.app.repl import Repl
from codefab.interpreter import Interpreter, InterpretResult


def test_빈_입력_목록이면_아무것도_실행하지_않는다(mocker):
    interpreter = mocker.Mock(spec=Interpreter)
    calls = []
    repl = Repl(interpreter=interpreter, output=calls.append)

    repl.run([])

    assert calls == []
    interpreter.interpret.assert_not_called()


def test_각_줄_입력_전에_prompt가_output으로_전달된다(mocker):
    interpreter = mocker.Mock(spec=Interpreter)
    interpreter.interpret.return_value = InterpretResult(output=[])
    calls = []
    repl = Repl(interpreter=interpreter, output=calls.append, prompt="laugh> ")

    repl.run(["첫줄;", "둘째줄;"])

    assert calls == ["laugh> ", "laugh> "]


def test_각_줄마다_interpret가_한_번씩_호출된다(mocker):
    interpreter = mocker.Mock(spec=Interpreter)
    interpreter.interpret.return_value = InterpretResult(output=[])
    repl = Repl(interpreter=interpreter, output=lambda _msg: None)

    repl.run(["첫줄;", "둘째줄;"])

    assert interpreter.interpret.call_args_list == [
        mocker.call("첫줄;"),
        mocker.call("둘째줄;"),
    ]


def test_interpret_결과의_output_줄이_순서대로_output_콜백에_전달된다(mocker):
    interpreter = mocker.Mock(spec=Interpreter)
    interpreter.interpret.return_value = InterpretResult(output=["1", "2"])
    calls = []
    repl = Repl(interpreter=interpreter, output=calls.append)

    repl.run_source("출력 1; 출력 2;")

    assert calls == ["1", "2"]


def test_interpret_결과에_error가_있으면_output_뒤에_이어서_전달된다(mocker):
    interpreter = mocker.Mock(spec=Interpreter)
    interpreter.interpret.return_value = InterpretResult(
        output=["1"], error="실행 오류 (줄 1): 오류"
    )
    calls = []
    repl = Repl(interpreter=interpreter, output=calls.append)

    repl.run_source("잘못된 문장")

    assert calls == ["1", "실행 오류 (줄 1): 오류"]


def test_error가_없으면_output_콜백에_error가_전달되지_않는다(mocker):
    interpreter = mocker.Mock(spec=Interpreter)
    interpreter.interpret.return_value = InterpretResult(output=["5"])
    calls = []
    repl = Repl(interpreter=interpreter, output=calls.append)

    repl.run_source("출력 5;")

    assert calls == ["5"]


def test_같은_interpreter_인스턴스가_여러_줄에_걸쳐_재사용된다(mocker):
    interpreter = mocker.Mock(spec=Interpreter)
    interpreter.interpret.return_value = InterpretResult(output=[])
    repl = Repl(interpreter=interpreter, output=lambda _msg: None)

    repl.run(["첫줄;", "둘째줄;"])

    assert repl._interpreter is interpreter
