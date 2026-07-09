import io

import pytest

from codefab.app.repl import Repl, main
from codefab.interpreter import Interpreter, InterpretResult


def test_빈_입력_목록이어도_프롬프트는_한_번_출력된다(mocker):
    # 실제 터미널에서는 입력이 더 있을지 미리 알 수 없으므로, EOF를 만나기 전에
    # 프롬프트부터 먼저 보여줘야 한다.
    interpreter = mocker.Mock(spec=Interpreter)
    calls = []
    repl = Repl(interpreter=interpreter, output=calls.append)

    repl.run([])

    assert calls == ["> "]
    interpreter.interpret.assert_not_called()


def test_각_줄을_읽기_전에_prompt가_먼저_output으로_전달된다(mocker):
    interpreter = mocker.Mock(spec=Interpreter)
    interpreter.interpret.return_value = InterpretResult(output=[])
    calls = []
    repl = Repl(interpreter=interpreter, output=calls.append, prompt="laugh> ")

    repl.run(["첫줄;", "둘째줄;"])

    # 마지막 줄 처리 후에도 다음 입력을 기다리며 프롬프트를 한 번 더 출력한다.
    assert calls == ["laugh> ", "laugh> ", "laugh> "]


def test_기본_output_사용시_프롬프트_뒤에_줄바꿈이_없다(mocker, capsys):
    # output 콜백을 안 넘기면(실제 터미널 사용 시) 프롬프트가 print() 기본 동작처럼
    # 줄바꿈되면 안 되고, 입력이 같은 줄에 이어져야 한다.
    interpreter = mocker.Mock(spec=Interpreter)
    interpreter.interpret.return_value = InterpretResult(output=["1"])
    repl = Repl(interpreter=interpreter)

    repl.run(["출력 1;"])

    captured = capsys.readouterr()
    assert captured.out == "> 1\n> "


@pytest.mark.parametrize("종료_명령", ["exit", "quit"])
def test_종료_명령_입력시_반복을_종료하고_실행하지_않는다(mocker, 종료_명령):
    interpreter = mocker.Mock(spec=Interpreter)
    calls = []
    repl = Repl(interpreter=interpreter, output=calls.append)

    repl.run([종료_명령, "출력 1;"])

    assert calls == ["> "]
    interpreter.interpret.assert_not_called()


@pytest.mark.parametrize(
    "lines, joined_source",
    [
        (["{", "출력 1;", "}"], "{\n출력 1;\n}"),
        (["출력 (1 +", "2);"], "출력 (1 +\n2);"),
        (["arr[", "0] = 10;"], "arr[\n0] = 10;"),
        (['출력 "hello', 'world";'], '출력 "hello\nworld";'),
    ],
    ids=["중괄호", "소괄호", "대괄호", "문자열"],
)
def test_안_닫힌_괄호나_문자열은_다음_줄까지_이어받아서_한번에_interpret한다(
    mocker, lines, joined_source
):
    interpreter = mocker.Mock(spec=Interpreter)
    interpreter.interpret.return_value = InterpretResult(output=[])
    repl = Repl(interpreter=interpreter, output=lambda _msg: None)

    repl.run(lines)

    interpreter.interpret.assert_called_once_with(joined_source)


def test_괄호가_안_닫혀있는_동안은_이어짐_프롬프트가_출력된다(mocker):
    interpreter = mocker.Mock(spec=Interpreter)
    interpreter.interpret.return_value = InterpretResult(output=[])
    calls = []
    repl = Repl(interpreter=interpreter, output=calls.append)

    repl.run(["{", "출력 1;", "}"])

    assert calls == ["> ", "... ", "... ", "> "]


def test_EOF에_도달하면_남은_버퍼를_실행해서_에러를_보여준다(mocker):
    interpreter = mocker.Mock(spec=Interpreter)
    interpreter.interpret.return_value = InterpretResult(
        output=[], error="에러: 닫는 괄호가 없습니다"
    )
    calls = []
    repl = Repl(interpreter=interpreter, output=calls.append)

    repl.run(["출력 (1 + 2;"])

    interpreter.interpret.assert_called_once_with("출력 (1 + 2;")
    assert "에러: 닫는 괄호가 없습니다" in calls


def test_만약_다음_줄에_아니면이_오면_하나로_합쳐서_interpret한다(mocker):
    interpreter = mocker.Mock(spec=Interpreter)
    interpreter.interpret.return_value = InterpretResult(output=[])
    repl = Repl(interpreter=interpreter, output=lambda _msg: None)

    repl.run(["만약 (참) {", '  출력 "hi";', "}", "아니면 {", '  출력 "bye";', "}"])

    interpreter.interpret.assert_called_once_with(
        '만약 (참) {\n  출력 "hi";\n}\n아니면 {\n  출력 "bye";\n}'
    )


def test_만약_다음_줄에_아니면이_없으면_따로_실행되고_그_줄은_새_명령으로_이어진다(
    mocker,
):
    interpreter = mocker.Mock(spec=Interpreter)
    interpreter.interpret.return_value = InterpretResult(output=[])
    repl = Repl(interpreter=interpreter, output=lambda _msg: None)

    repl.run(["만약 (참) {", '  출력 "hi";', "}", "출력 2;"])

    assert interpreter.interpret.call_args_list == [
        mocker.call('만약 (참) {\n  출력 "hi";\n}'),
        mocker.call("출력 2;"),
    ]


def test_아니면_대기중_EOF가_오면_보류한_만약을_실행한다(mocker):
    interpreter = mocker.Mock(spec=Interpreter)
    interpreter.interpret.return_value = InterpretResult(output=[])
    repl = Repl(interpreter=interpreter, output=lambda _msg: None)

    repl.run(["만약 (참) {", '  출력 "hi";', "}"])

    interpreter.interpret.assert_called_once_with('만약 (참) {\n  출력 "hi";\n}')


def test_아니면_대기중_exit가_오면_보류한_버퍼를_버리고_바로_종료한다(mocker):
    interpreter = mocker.Mock(spec=Interpreter)
    repl = Repl(interpreter=interpreter, output=lambda _msg: None)

    repl.run(["만약 (참) {", '  출력 "hi";', "}", "exit", '출력 "다시_실행되면_안됨";'])

    interpreter.interpret.assert_not_called()


@pytest.mark.parametrize("종료_명령", ["exit", "quit"])
def test_여러_줄_이어받는_중에도_종료_명령이_오면_버퍼를_버리고_바로_종료한다(
    mocker, 종료_명령
):
    interpreter = mocker.Mock(spec=Interpreter)
    repl = Repl(interpreter=interpreter, output=lambda _msg: None)

    repl.run(["{", '  출력 "hi";', 종료_명령, "}"])

    interpreter.interpret.assert_not_called()


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


def test_main이_stdin_각_줄의_개행문자를_제거해_repl_run에_전달한다(mocker):
    mocker.patch("sys.stdin", io.StringIO("첫줄;\n둘째줄;\n"))
    repl_instance = mocker.Mock(spec=Repl)
    repl_cls = mocker.patch("codefab.app.repl.Repl", return_value=repl_instance)

    exit_code = main()

    repl_cls.assert_called_once()
    assert list(repl_instance.run.call_args.args[0]) == ["첫줄;", "둘째줄;"]
    assert exit_code == 0


def test_main은_KeyboardInterrupt가_발생해도_0을_반환한다(mocker):
    repl_instance = mocker.Mock(spec=Repl)
    repl_instance.run.side_effect = KeyboardInterrupt
    mocker.patch("codefab.app.repl.Repl", return_value=repl_instance)

    exit_code = main()

    assert exit_code == 0
