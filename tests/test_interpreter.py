from codefab.assembler.assembler import Assembler
from codefab.assembler.errors import ParseError
from codefab.ast_nodes import Literal as ExprLiteral
from codefab.ast_nodes import PrintStmt
from codefab.checker import Checker
from codefab.error import DuplicateVariableError, ExecutorRuntimeError
from codefab.executor_unit import ExecutorUnit
from codefab.interpreter import Interpreter


def test_알수없는_예외가_발생해도_전파되지_않고_에러메시지로_반환된다(mocker):
    assembler = mocker.Mock(spec=Assembler)
    assembler.assemble.side_effect = AttributeError("의도적으로 발생시킨 오류")
    interpreter = Interpreter(assembler=assembler)

    result = interpreter.interpret("아무거나;")

    assert result.output == []
    assert "의도적으로 발생시킨 오류" in result.error


def test_source가_assembler에_그대로_전달된다(mocker):
    assembler = mocker.Mock(spec=Assembler)
    assembler.assemble.return_value = []
    interpreter = Interpreter(assembler=assembler)

    interpreter.interpret("1;")
    interpreter.interpret("2;")

    assert assembler.assemble.call_args_list == [mocker.call("1;"), mocker.call("2;")]


def test_assembler가_반환한_문장이_checker에_전달된다(mocker):
    statements = ["stmt-1", "stmt-2"]
    assembler = mocker.Mock(spec=Assembler)
    assembler.assemble.return_value = statements
    checker = mocker.Mock(spec=Checker)
    interpreter = Interpreter(assembler=assembler, checker=checker)

    interpreter.interpret("아무거나;")

    checker.resolve.assert_called_once_with(statements)


def test_checker_통과후_executor에도_동일한_statement가_전달된다(mocker):
    statements = ["stmt-1", "stmt-2"]
    order = []
    assembler = mocker.Mock(spec=Assembler)
    assembler.assemble.return_value = statements
    checker = mocker.Mock(spec=Checker)
    checker.resolve.side_effect = lambda stmts: order.append("checker")
    executor = mocker.Mock(spec=ExecutorUnit)
    executor.execute.side_effect = lambda stmts: order.append("executor")
    interpreter = Interpreter(assembler=assembler, checker=checker, executor=executor)

    interpreter.interpret("아무거나;")

    executor.execute.assert_called_once_with(statements)
    assert order == ["checker", "executor"]


def test_ParseError가_발생하면_에러메시지를_반환한다(mocker):
    assembler = mocker.Mock(spec=Assembler)
    assembler.assemble.side_effect = ParseError("값 뒤에 ';'가 필요합니다.", line=1)
    interpreter = Interpreter(assembler=assembler)

    result = interpreter.interpret("잘못된 문장")

    assert "구문 오류" in result.error
    assert "값 뒤에 ';'가 필요합니다." in result.error


def test_Checker_CheckerError가_발생하면_에러메시지를_반환한다(mocker):
    assembler = mocker.Mock(spec=Assembler)
    assembler.assemble.return_value = []
    checker = mocker.Mock(spec=Checker)
    checker.resolve.side_effect = DuplicateVariableError()
    interpreter = Interpreter(assembler=assembler, checker=checker)

    result = interpreter.interpret("아무거나;")

    assert "검사 오류" in result.error
    assert "이미 선언된 변수입니다." in result.error


def test_ExecutorRuntimeError가_발생하면_줄번호를_포함해_반환한다(mocker):
    assembler = mocker.Mock(spec=Assembler)
    assembler.assemble.return_value = []
    executor = mocker.Mock(spec=ExecutorUnit)
    executor.execute.side_effect = ExecutorRuntimeError("0으로 나눈 오류", line=3)
    interpreter = Interpreter(
        assembler=assembler,
        checker=mocker.Mock(spec=Checker),
        executor=executor,
    )

    result = interpreter.interpret("아무거나;")

    assert "실행 오류" in result.error
    assert "3" in result.error
    assert "0으로 나눈 오류" in result.error


def test_같은_executor_인스턴스가_여러_호출에_걸쳐_재사용된다(mocker):
    assembler = mocker.Mock(spec=Assembler)
    assembler.assemble.return_value = ["stmt"]
    executor = mocker.Mock(spec=ExecutorUnit)
    interpreter = Interpreter(
        assembler=assembler, checker=mocker.Mock(spec=Checker), executor=executor
    )

    interpreter.interpret("첫줄;")
    interpreter.interpret("둘째줄;")

    assert executor.execute.call_args_list == [
        mocker.call(["stmt"]),
        mocker.call(["stmt"]),
    ]


def test_한_호출에서_선언한_변수를_다음_호출에서_참조할_수_있다(mocker):
    interpreter = Interpreter(assembler=Assembler(), checker=mocker.Mock(spec=Checker))

    interpreter.interpret("변수 a = 5;")
    interpreter.interpret("변수 b = a;")

    assert interpreter._executor.environment.values == {"a": 5.0, "b": 5.0}


def test_print_statement_실행결과가_output으로_반환된다(capsys, mocker):
    assembler = mocker.Mock(spec=Assembler)
    assembler.assemble.return_value = [PrintStmt(expression=ExprLiteral(5.0))]
    interpreter = Interpreter(assembler=assembler, checker=mocker.Mock(spec=Checker))

    result = interpreter.interpret("출력 5;")

    assert result.output == ["5"]
    assert result.error is None
    assert capsys.readouterr().out == ""


def test_실행_중_예외가_발생해도_그_전에_출력된_내용은_반환된다(mocker):
    assembler = mocker.Mock(spec=Assembler)
    assembler.assemble.return_value = [PrintStmt(expression=ExprLiteral(1.0)), object()]
    interpreter = Interpreter(assembler=assembler, checker=mocker.Mock(spec=Checker))

    result = interpreter.interpret("출력 1; 잘못된문장")

    assert result.output == ["1"]
    assert "실행 오류" in result.error


def test_assembler를_주입하지_않으면_기본_assembler가_사용된다(mocker):
    interpreter = Interpreter(checker=mocker.Mock(spec=Checker))

    result = interpreter.interpret("변수 a = 3; 출력 a;")

    assert result.output == ["3"]
    assert result.error is None
