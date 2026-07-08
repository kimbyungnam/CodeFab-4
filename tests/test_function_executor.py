import pytest

from codefab.ast_nodes import (
    Binary,
    Call,
    ExpressionStmt,
    FunctionStmt,
    IfStmt,
    Literal,
    PrintStmt,
    ReturnStmt,
    Variable,
    VarStmt,
)
from codefab.error import ArgumentCountMismatchError, NotCallableError
from codefab.function_executor import FunctionExecutorUnit, ReturnSignal, UserFunction
from codefab.tokens import Token, TokenType


def make_identifier_token(lexeme: str, line: int = 1) -> Token:
    return Token(type=TokenType.IDENTIFIER, lexeme=lexeme, literal=None, line=line)


def make_paren_token(line: int = 1) -> Token:
    return Token(type=TokenType.RIGHT_PAREN, lexeme=")", literal=None, line=line)


def make_variable(name_lexeme: str) -> Variable:
    return Variable(name=make_identifier_token(name_lexeme))


def make_binary(left, operator_lexeme, right) -> Binary:
    operator_type = {
        "+": TokenType.PLUS,
        "-": TokenType.MINUS,
        "*": TokenType.STAR,
        "<=": TokenType.LESS_EQUAL,
    }[operator_lexeme]
    return Binary(
        left=left,
        operator=Token(operator_type, operator_lexeme, literal=None, line=1),
        right=right,
    )


def make_function_stmt(name, params, body) -> FunctionStmt:
    return FunctionStmt(
        name=make_identifier_token(name),
        params=[make_identifier_token(p) for p in params],
        body=body,
    )


def make_call(callee, arguments, line=1) -> Call:
    return Call(callee=callee, paren=make_paren_token(line), arguments=arguments)


def run_and_capture_prints(capsys, statements) -> list:
    FunctionExecutorUnit().execute(statements)
    return capsys.readouterr().out.splitlines()


def test_함수_선언은_environment에_UserFunction으로_저장된다():
    function_stmt = make_function_stmt("add", ["a", "b"], body=[])
    executor = FunctionExecutorUnit()

    executor.execute([function_stmt])

    stored = executor.environment.values["add"]
    assert isinstance(stored, UserFunction)
    assert stored.arity == 2


def test_함수_호출은_반환값을_돌려준다(capsys):
    # 함수 add(a, b) { 반환 a + b; } 출력 add(3, 7);
    function_stmt = make_function_stmt(
        "add",
        ["a", "b"],
        body=[
            ReturnStmt(
                keyword=Token(TokenType.RETURN, "반환", None, 1),
                value=make_binary(make_variable("a"), "+", make_variable("b")),
            )
        ],
    )
    call_stmt = PrintStmt(make_call(make_variable("add"), [Literal(3.0), Literal(7.0)]))

    assert run_and_capture_prints(capsys, [function_stmt, call_stmt]) == ["10"]


def test_반환값이_없는_반환문은_None을_돌려준다():
    # 함수 noop() { 반환; }
    function_stmt = make_function_stmt(
        "noop",
        [],
        body=[ReturnStmt(keyword=Token(TokenType.RETURN, "반환", None, 1), value=None)],
    )
    executor = FunctionExecutorUnit()
    executor.execute([function_stmt])

    result = executor._evaluate_call(make_call(make_variable("noop"), []))

    assert result is None


def test_본문에_반환문이_없으면_None을_돌려준다():
    # 함수 noop() { }
    function_stmt = make_function_stmt("noop", [], body=[])
    executor = FunctionExecutorUnit()
    executor.execute([function_stmt])

    result = executor._evaluate_call(make_call(make_variable("noop"), []))

    assert result is None


def test_인자로_전달한_값을_함수_내부에서_사용할_수_있다(capsys):
    # 함수 square(n) { 출력 n * n; } square(4);
    function_stmt = make_function_stmt(
        "square",
        ["n"],
        body=[PrintStmt(make_binary(make_variable("n"), "*", make_variable("n")))],
    )
    call_stmt = ExpressionStmt(make_call(make_variable("square"), [Literal(4.0)]))

    assert run_and_capture_prints(capsys, [function_stmt, call_stmt]) == ["16"]


def test_재귀_호출로_팩토리얼을_계산한다(capsys):
    # 함수 fact(n) { 만약 (n <= 1) 반환 1; 반환 n * fact(n - 1); } 출력 fact(5);
    n = make_variable("n")
    fact_body = [
        IfStmt(
            condition=make_binary(n, "<=", Literal(1.0)),
            then_branch=ReturnStmt(
                keyword=Token(TokenType.RETURN, "반환", None, 1), value=Literal(1.0)
            ),
            else_branch=None,
        ),
        ReturnStmt(
            keyword=Token(TokenType.RETURN, "반환", None, 2),
            value=make_binary(
                make_variable("n"),
                "*",
                make_call(
                    make_variable("fact"),
                    [make_binary(make_variable("n"), "-", Literal(1.0))],
                ),
            ),
        ),
    ]
    function_stmt = make_function_stmt("fact", ["n"], body=fact_body)
    call_stmt = PrintStmt(make_call(make_variable("fact"), [Literal(5.0)]))

    assert run_and_capture_prints(capsys, [function_stmt, call_stmt]) == ["120"]


def test_함수_호출_결과를_변수에_대입할_수_있다(capsys):
    # 함수 add(a, b) { 반환 a + b; } 변수 ret = add(3, 7); 출력 ret;
    function_stmt = make_function_stmt(
        "add",
        ["a", "b"],
        body=[
            ReturnStmt(
                keyword=Token(TokenType.RETURN, "반환", None, 1),
                value=make_binary(make_variable("a"), "+", make_variable("b")),
            )
        ],
    )
    statements = [
        function_stmt,
        VarStmt(
            name=make_identifier_token("ret"),
            initializer=make_call(make_variable("add"), [Literal(3.0), Literal(7.0)]),
        ),
        PrintStmt(make_variable("ret")),
    ]

    assert run_and_capture_prints(capsys, statements) == ["10"]


def test_함수가_아닌_대상을_호출하면_에러():
    # 변수 x = "hello"; x();
    statements = [
        VarStmt(name=make_identifier_token("x"), initializer=Literal("hello")),
    ]
    executor = FunctionExecutorUnit()
    executor.execute(statements)

    with pytest.raises(NotCallableError) as exc_info:
        executor._evaluate_call(make_call(make_variable("x"), [], line=5))

    assert exc_info.value.message == "호출 가능한 대상(함수)이 아닙니다."
    assert exc_info.value.line == 5


def test_인자_개수가_파라미터보다_적으면_에러():
    # 함수 foo(a, b, c) { 반환 a; } foo(1, 2);
    function_stmt = make_function_stmt(
        "foo",
        ["a", "b", "c"],
        body=[
            ReturnStmt(
                keyword=Token(TokenType.RETURN, "반환", None, 1), value=Literal(1.0)
            )
        ],
    )
    executor = FunctionExecutorUnit()
    executor.execute([function_stmt])

    with pytest.raises(ArgumentCountMismatchError) as exc_info:
        executor._evaluate_call(
            make_call(make_variable("foo"), [Literal(1.0), Literal(2.0)], line=7)
        )

    assert "필요: 3개" in exc_info.value.message
    assert "전달: 2개" in exc_info.value.message
    assert exc_info.value.line == 7


def test_인자_개수가_파라미터보다_많으면_에러():
    # 함수 add(a, b) { 반환 a + b; } add(1, 2, 3);
    function_stmt = make_function_stmt(
        "add",
        ["a", "b"],
        body=[
            ReturnStmt(
                keyword=Token(TokenType.RETURN, "반환", None, 1), value=Literal(1.0)
            )
        ],
    )
    executor = FunctionExecutorUnit()
    executor.execute([function_stmt])

    with pytest.raises(ArgumentCountMismatchError):
        executor._evaluate_call(
            make_call(make_variable("add"), [Literal(1.0), Literal(2.0), Literal(3.0)])
        )


def test_기존_리터럴_이항연산_출력_동작은_그대로_유지된다(capsys):
    # FunctionExecutorUnit이 ExecutorUnit의 기존 동작을 깨지 않는지 확인
    statement = PrintStmt(make_binary(Literal(3.0), "+", Literal(2.0)))

    assert run_and_capture_prints(capsys, [statement]) == ["5"]


def test_클로저는_선언_당시의_environment를_기억한다(capsys):
    # 변수 base = 10; 함수 addBase(n) { 반환 base + n; } 출력 addBase(5);
    statements = [
        VarStmt(name=make_identifier_token("base"), initializer=Literal(10.0)),
        make_function_stmt(
            "addBase",
            ["n"],
            body=[
                ReturnStmt(
                    keyword=Token(TokenType.RETURN, "반환", None, 1),
                    value=make_binary(make_variable("base"), "+", make_variable("n")),
                )
            ],
        ),
        PrintStmt(make_call(make_variable("addBase"), [Literal(5.0)])),
    ]

    assert run_and_capture_prints(capsys, statements) == ["15"]


def test_return_signal은_지정한_값을_보관한다():
    signal = ReturnSignal(42.0)

    assert signal.value == 42.0
