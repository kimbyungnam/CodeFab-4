import pytest

from codefab.assembler.function_assembler import FunctionAssembler
from codefab.checker import FunctionChecker
from codefab.errors import (
    DuplicateParameterError,
    DuplicateVariableError,
    ReturnInInitializerError,
    ReturnOutsideFunctionError,
)
from codefab.tokens import Token, TokenType


def make_token(lexeme, line=1):
    return Token(type=TokenType.IDENTIFIER, lexeme=lexeme, literal=None, line=line)


@pytest.fixture
def sut():
    return FunctionChecker()


@pytest.fixture
def make_function_stmt(mocker):
    def _make(name_lexeme, params, body, line=1):
        param_tokens = [make_token(p, line) for p in params]
        function_stmt = mocker.Mock(params=param_tokens, body=body)
        function_stmt.name = make_token(name_lexeme, line)
        function_stmt.accept.side_effect = lambda visitor: visitor.visit_function_stmt(
            function_stmt
        )
        return function_stmt

    return _make


@pytest.fixture
def make_return_stmt(mocker):
    def _make(value=None, line=1):
        return_stmt = mocker.Mock(value=value)
        return_stmt.keyword = make_token("반환", line)
        return_stmt.accept.side_effect = lambda visitor: visitor.visit_return_stmt(
            return_stmt
        )
        return return_stmt

    return _make


@pytest.fixture
def make_call(mocker):
    def _make(callee, arguments=None):
        call = mocker.Mock(callee=callee, arguments=arguments or [])
        call.accept.side_effect = lambda visitor: visitor.visit_call(call)
        return call

    return _make


@pytest.fixture
def make_variable(mocker):
    def _make(lexeme, line=1):
        variable = mocker.Mock()
        variable.name = make_token(lexeme, line)
        variable.accept.side_effect = lambda visitor: visitor.visit_variable(variable)
        return variable

    return _make


@pytest.fixture
def make_exp_stmt(mocker):
    def _make(expression):
        exp_stmt = mocker.Mock(expression=expression)
        exp_stmt.accept.side_effect = lambda visitor: visitor.visit_expression_stmt(
            exp_stmt
        )
        return exp_stmt

    return _make


def test_함수_선언은_현재_스코프에_이름을_등록한다(sut, make_function_stmt):
    # 함수 add(a, b) { }
    function_stmt = make_function_stmt("add", ["a", "b"], body=[])

    sut.resolve([function_stmt])

    assert sut.declared == {"add"}


def test_함수_이름이_같은_스코프에서_중복되면_에러(sut, make_function_stmt):
    # 함수 add() { } 함수 add() { }
    first = make_function_stmt("add", [], body=[], line=1)
    second = make_function_stmt("add", [], body=[], line=2)

    with pytest.raises(DuplicateVariableError, match="이미 선언된 변수입니다."):
        sut.resolve([first, second])


def test_파라미터_이름이_중복되면_에러(sut, make_function_stmt):
    # 함수 foo(a, a) { }
    function_stmt = make_function_stmt("foo", ["a", "a"], body=[])

    with pytest.raises(
        DuplicateParameterError, match="파라미터 이름이 중복되었습니다."
    ):
        sut.resolve([function_stmt])


def test_함수_본문_내부에서는_반환을_사용할_수_있다(
    sut, make_function_stmt, make_return_stmt
):
    # 함수 foo() { 반환 5; }
    return_stmt = make_return_stmt(value=None)
    function_stmt = make_function_stmt("foo", [], body=[return_stmt])

    sut.resolve([function_stmt])  # 에러 없이 통과해야 한다

    assert sut.function_depth == 0  # 함수 검사가 끝나면 depth가 복원된다


def test_함수_외부에서_반환을_사용하면_에러(sut, make_return_stmt):
    # 반환 5;
    return_stmt = make_return_stmt(value=None, line=3)

    with pytest.raises(
        ReturnOutsideFunctionError, match="함수 외부에서는 '반환'을 사용할 수 없습니다."
    ):
        sut.resolve([return_stmt])


def test_반환값이_있으면_그_표현식도_방문한다(
    sut, make_function_stmt, make_return_stmt, make_variable
):
    # 함수 foo() { 반환 a; }
    variable_a = make_variable("a")
    return_stmt = make_return_stmt(value=variable_a)
    function_stmt = make_function_stmt("foo", [], body=[return_stmt])

    sut.resolve([function_stmt])

    variable_a.accept.assert_called_once_with(sut)


def test_함수_본문은_파라미터_스코프에서_변수를_참조할_수_있다(
    sut, make_function_stmt, make_return_stmt, make_variable
):
    # 함수 add(a, b) { 반환 a; }
    variable_a = make_variable("a")
    return_stmt = make_return_stmt(value=variable_a)
    function_stmt = make_function_stmt("add", ["a", "b"], body=[return_stmt])

    sut.resolve([function_stmt])  # UndefinedVariableError 없이 통과해야 한다


def test_함수_호출_표현식은_callee와_인자를_모두_방문한다(
    sut, make_call, make_variable, make_exp_stmt
):
    # add(x, y);
    callee = make_variable("add")
    arg_x = make_variable("x")
    arg_y = make_variable("y")
    call = make_call(callee, arguments=[arg_x, arg_y])
    exp_stmt = make_exp_stmt(call)

    sut.resolve([exp_stmt])

    callee.accept.assert_called_once_with(sut)
    arg_x.accept.assert_called_once_with(sut)
    arg_y.accept.assert_called_once_with(sut)


def test_인자가_없는_호출도_에러_없이_방문된다(
    sut, make_call, make_variable, make_exp_stmt
):
    # noop();
    callee = make_variable("noop")
    call = make_call(callee, arguments=[])
    exp_stmt = make_exp_stmt(call)

    sut.resolve([exp_stmt])

    callee.accept.assert_called_once_with(sut)


def test_재귀_호출은_함수_본문에서_자기_이름을_참조할_수_있다(
    sut, make_function_stmt, make_return_stmt, make_call, make_variable, make_exp_stmt
):
    # 함수 fact(n) { 반환 fact(n); }
    self_reference = make_variable("fact")
    call = make_call(self_reference, arguments=[make_variable("n")])
    return_stmt = make_return_stmt(value=call)
    function_stmt = make_function_stmt("fact", ["n"], body=[return_stmt])

    sut.resolve([function_stmt])  # 재귀 호출도 에러 없이 통과해야 한다

    self_reference.accept.assert_called_once_with(sut)


def test_클래스_메서드_내부의_반환은_함수_외부_에러가_아니다():
    # 클래스 Robot { move() { 반환 5; } }
    statements = FunctionAssembler().assemble(
        """
        클래스 Robot {
            move() {
                반환 5;
            }
        }
        """
    )

    FunctionChecker().resolve(statements)  # 에러 없이 통과해야 한다


def test_생성자_내부의_반환은_여전히_에러다():
    # 클래스 Robot { init() { 반환 5; } }
    statements = FunctionAssembler().assemble(
        """
        클래스 Robot {
            init() {
                반환 5;
            }
        }
        """
    )

    with pytest.raises(ReturnInInitializerError):
        FunctionChecker().resolve(statements)


def test_중첩_함수_선언도_각자의_함수_depth를_올바르게_복원한다(
    sut, make_function_stmt, make_return_stmt
):
    # 함수 outer() { 함수 inner() { 반환 1; } 반환 2; }
    inner_return = make_return_stmt(value=None)
    inner_function = make_function_stmt("inner", [], body=[inner_return])
    outer_return = make_return_stmt(value=None)
    outer_function = make_function_stmt(
        "outer", [], body=[inner_function, outer_return]
    )

    sut.resolve([outer_function])

    assert sut.function_depth == 0
