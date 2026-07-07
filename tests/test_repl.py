from codefab.app.repl import Repl
from codefab.assembler.errors import ParseError
from codefab.assembler.expr import Literal as ExprLiteral
from codefab.assembler.expr import Variable as ExprVariable
from codefab.ast_nodes import PrintStmt, VarStmt
from codefab.checker import Checker
from codefab.executor_unit import ExecutorRuntimeError, ExecutorUnit
from codefab.tokenizer import Tokenizer
from codefab.tokens import Token, TokenType


def _unused_factory(tokens):
    raise AssertionError("create_statement_parser should not be called")


def test_빈_입력_목록이면_아무것도_실행하지_않는다():
    calls = []
    repl = Repl(create_statement_parser=_unused_factory, output=calls.append)

    repl.run([])

    assert calls == []


def test_알수없는_예외가_발생해도_루프를_죽이지_않고_다음_입력을_처리한다():
    processed = []

    def factory(tokens):
        if not processed:
            processed.append("first")
            raise AttributeError("의도적으로 발생시킨 오류")
        processed.append("second")
        raise AssertionError("stop before assembler stage")

    repl = Repl(create_statement_parser=factory, output=lambda _msg: None)

    repl.run(["첫줄;", "둘째줄;"])

    assert processed == ["first", "second"]


def test_create_statement_parser가_매_줄마다_새로_생성된다():
    factory_calls = []

    def factory(tokens):
        factory_calls.append(tokens)
        raise AssertionError("assembler 단계까지 가지 않아도 됨")

    repl = Repl(create_statement_parser=factory, output=lambda _msg: None)

    repl.run(["1;", "2;"])

    assert factory_calls == [
        Tokenizer("1;").scan_tokens(),
        Tokenizer("2;").scan_tokens(),
    ]


class _FakeStatementParser:
    def __init__(self, statements):
        self._statements = list(statements)

    def is_at_end(self):
        return len(self._statements) == 0

    def parse_statement(self):
        return self._statements.pop(0)


def test_fake_statement_parser가_반환한_문장이_checker에_전달된다(mocker):
    statements = ["stmt-1", "stmt-2"]
    checker = mocker.Mock(spec=Checker)
    repl = Repl(
        create_statement_parser=lambda tokens: _FakeStatementParser(statements),
        checker=checker,
        output=lambda _msg: None,
    )

    repl.run_source("아무거나;")

    checker.resolve.assert_called_once_with(statements)


def test_checker_통과후_executor에도_동일한_statement가_전달된다(mocker):
    statements = ["stmt-1", "stmt-2"]
    order = []
    checker = mocker.Mock(spec=Checker)
    checker.resolve.side_effect = lambda stmts: order.append("checker")
    executor = mocker.Mock(spec=ExecutorUnit)
    executor.execute.side_effect = lambda stmts: order.append("executor")
    repl = Repl(
        create_statement_parser=lambda tokens: _FakeStatementParser(statements),
        checker=checker,
        executor=executor,
        output=lambda _msg: None,
    )

    repl.run_source("아무거나;")

    executor.execute.assert_called_once_with(statements)
    assert order == ["checker", "executor"]


def test_ParseError가_발생하면_에러메시지를_출력하고_계속한다():
    calls = []

    def factory(tokens):
        raise ParseError("값 뒤에 ';'가 필요합니다.", line=1)

    repl = Repl(create_statement_parser=factory, output=calls.append)

    repl.run(["잘못된 문장"])

    assert len(calls) == 2
    assert "구문 오류" in calls[1]
    assert "값 뒤에 ';'가 필요합니다." in calls[1]


def test_Checker_ValueError가_발생하면_에러메시지를_출력하고_계속한다(mocker):
    calls = []
    checker = mocker.Mock(spec=Checker)
    checker.resolve.side_effect = ValueError("이미 선언된 변수입니다.")
    repl = Repl(
        create_statement_parser=lambda tokens: _FakeStatementParser([]),
        checker=checker,
        output=calls.append,
    )

    repl.run(["아무거나;"])

    assert len(calls) == 2
    assert "검사 오류" in calls[1]
    assert "이미 선언된 변수입니다." in calls[1]


def test_ExecutorRuntimeError가_발생하면_줄번호를_포함해_출력한다(mocker):
    calls = []
    executor = mocker.Mock(spec=ExecutorUnit)
    executor.execute.side_effect = ExecutorRuntimeError("0으로 나눈 오류", line=3)
    repl = Repl(
        create_statement_parser=lambda tokens: _FakeStatementParser([]),
        checker=mocker.Mock(spec=Checker),
        executor=executor,
        output=calls.append,
    )

    repl.run(["아무거나;"])

    assert len(calls) == 2
    assert "실행 오류" in calls[1]
    assert "3" in calls[1]
    assert "0으로 나눈 오류" in calls[1]


def test_같은_executor_인스턴스가_여러_줄에_걸쳐_재사용된다(mocker):
    executor = mocker.Mock(spec=ExecutorUnit)
    repl = Repl(
        create_statement_parser=lambda tokens: _FakeStatementParser(["stmt"]),
        checker=mocker.Mock(spec=Checker),
        executor=executor,
        output=lambda _msg: None,
    )

    repl.run(["첫줄;", "둘째줄;"])

    assert repl._executor is executor
    assert executor.execute.call_args_list == [
        mocker.call(["stmt"]),
        mocker.call(["stmt"]),
    ]


def test_한_줄에서_선언한_변수를_다음_줄에서_참조할_수_있다(mocker):
    a_token = Token(type=TokenType.IDENTIFIER, lexeme="a", literal=None, line=1)
    b_token = Token(type=TokenType.IDENTIFIER, lexeme="b", literal=None, line=1)
    statements_per_line = [
        [VarStmt(name=a_token, initializer=ExprLiteral(5.0))],
        [VarStmt(name=b_token, initializer=ExprVariable(name=a_token))],
    ]
    calls = []

    def factory(tokens):
        return _FakeStatementParser(statements_per_line.pop(0))

    repl = Repl(
        create_statement_parser=factory,
        checker=mocker.Mock(spec=Checker),
        output=calls.append,
    )

    repl.run(["변수 a = 5;", "변수 b = a;"])

    assert calls == ["> ", "> "]
    assert repl._executor.environment == {"a": 5.0, "b": 5.0}


def test_print_statement_실행결과가_output에_전달된다(capsys, mocker):
    statements = [PrintStmt(expression=ExprLiteral(5.0))]
    calls = []
    repl = Repl(
        create_statement_parser=lambda tokens: _FakeStatementParser(statements),
        checker=mocker.Mock(spec=Checker),
        output=calls.append,
    )

    repl.run_source("출력 5;")

    assert calls == ["5"]
    assert capsys.readouterr().out == ""


def test_실행_중_예외가_발생해도_그_전에_출력된_내용은_전달된다(mocker):
    statements = [PrintStmt(expression=ExprLiteral(1.0)), object()]
    calls = []
    repl = Repl(
        create_statement_parser=lambda tokens: _FakeStatementParser(statements),
        checker=mocker.Mock(spec=Checker),
        output=calls.append,
    )

    repl.run_source("출력 1; 잘못된문장")

    assert calls[0] == "1"
    assert "실행 오류" in calls[1]


def test_tokenize를_주입하면_주입된_함수가_사용된다(mocker):
    fake_tokens = ["fake-token-1", "fake-token-2"]
    received_tokens = []

    def create_statement_parser(tokens):
        received_tokens.append(tokens)
        return _FakeStatementParser([])

    repl = Repl(
        create_statement_parser=create_statement_parser,
        tokenize=lambda source: fake_tokens,
        checker=mocker.Mock(spec=Checker),
        output=lambda _msg: None,
    )

    repl.run_source("아무 문자열이나 상관없음")

    assert received_tokens == [fake_tokens]


def test_각_줄_입력_전에_prompt가_output으로_전달된다(mocker):
    calls = []
    repl = Repl(
        create_statement_parser=lambda tokens: _FakeStatementParser([]),
        checker=mocker.Mock(spec=Checker),
        output=calls.append,
        prompt="laugh> ",
    )

    repl.run(["첫줄;", "둘째줄;"])

    assert calls == ["laugh> ", "laugh> "]
