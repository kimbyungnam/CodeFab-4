import pytest

from codefab.array_nodes import ArrayLiteral, IndexGet
from codefab.ast_nodes import (
    Binary,
    ExpressionStmt,
    Grouping,
    IfStmt,
    Literal,
    Logical,
    PrintStmt,
    Unary,
    Variable,
    VarStmt,
)
from codefab.optimizer import Optimizer
from codefab.tokens import Token, TokenType


def make_identifier_token(lexeme: str, line: int = 1) -> Token:
    return Token(type=TokenType.IDENTIFIER, lexeme=lexeme, literal=None, line=line)


def make_operator_token(token_type: TokenType, lexeme: str) -> Token:
    return Token(type=token_type, lexeme=lexeme, literal=None, line=1)


def test_리터럴_상수_이항연산은_하나의_리터럴로_접힌다(mocker):
    # 1 + 2
    left = mocker.Mock(spec=Literal, value=1.0)
    right = mocker.Mock(spec=Literal, value=2.0)
    expr = mocker.Mock(
        spec=Binary, left=left, operator=make_operator_token(TokenType.PLUS, "+"), right=right
    )
    stmt = mocker.Mock(spec=ExpressionStmt, expression=expr)

    Optimizer().optimize([stmt])

    assert stmt.expression == Literal(3.0)


def test_문자열_리터럴_덧셈도_접힌다(mocker):
    left = mocker.Mock(spec=Literal, value="a")
    right = mocker.Mock(spec=Literal, value="b")
    expr = mocker.Mock(
        spec=Binary, left=left, operator=make_operator_token(TokenType.PLUS, "+"), right=right
    )
    stmt = mocker.Mock(spec=ExpressionStmt, expression=expr)

    Optimizer().optimize([stmt])

    assert stmt.expression == Literal("ab")


def test_중첩된_상수_연산은_전부_접혀서_하나의_리터럴이_된다(mocker):
    # 1 + 2 * 3
    inner = mocker.Mock(
        spec=Binary,
        left=mocker.Mock(spec=Literal, value=2.0),
        operator=make_operator_token(TokenType.STAR, "*"),
        right=mocker.Mock(spec=Literal, value=3.0),
    )
    outer = mocker.Mock(
        spec=Binary,
        left=mocker.Mock(spec=Literal, value=1.0),
        operator=make_operator_token(TokenType.PLUS, "+"),
        right=inner,
    )
    stmt = mocker.Mock(spec=ExpressionStmt, expression=outer)

    Optimizer().optimize([stmt])

    assert stmt.expression == Literal(7.0)


def test_괄호로_감싼_상수도_접힌다(mocker):
    # (1 + 2)
    inner = mocker.Mock(
        spec=Binary,
        left=mocker.Mock(spec=Literal, value=1.0),
        operator=make_operator_token(TokenType.PLUS, "+"),
        right=mocker.Mock(spec=Literal, value=2.0),
    )
    stmt = mocker.Mock(spec=ExpressionStmt, expression=mocker.Mock(spec=Grouping, expression=inner))

    Optimizer().optimize([stmt])

    assert stmt.expression == Literal(3.0)


def test_단항_마이너스_상수는_접힌다(mocker):
    right = mocker.Mock(spec=Literal, value=3.0)
    expr = mocker.Mock(spec=Unary, operator=make_operator_token(TokenType.MINUS, "-"), right=right)
    stmt = mocker.Mock(spec=ExpressionStmt, expression=expr)

    Optimizer().optimize([stmt])

    assert stmt.expression == Literal(-3.0)


def test_단항_bang_상수는_접힌다(mocker):
    right = mocker.Mock(spec=Literal, value=False)
    expr = mocker.Mock(spec=Unary, operator=make_operator_token(TokenType.BANG, "!"), right=right)
    stmt = mocker.Mock(spec=ExpressionStmt, expression=expr)

    Optimizer().optimize([stmt])

    assert stmt.expression == Literal(True)


def test_변수가_포함된_연산은_접히지_않는다(mocker):
    variable = mocker.Mock(spec=Variable)
    expr = mocker.Mock(
        spec=Binary,
        left=variable,
        operator=make_operator_token(TokenType.PLUS, "+"),
        right=mocker.Mock(spec=Literal, value=1.0),
    )
    stmt = mocker.Mock(spec=ExpressionStmt, expression=expr)

    Optimizer().optimize([stmt])

    assert stmt.expression is expr
    assert stmt.expression.left is variable


def test_0으로_나누는_상수연산은_접지_않고_그대로_둔다(mocker):
    expr = mocker.Mock(
        spec=Binary,
        left=mocker.Mock(spec=Literal, value=1.0),
        operator=make_operator_token(TokenType.SLASH, "/"),
        right=mocker.Mock(spec=Literal, value=0.0),
    )
    stmt = mocker.Mock(spec=ExpressionStmt, expression=expr)

    Optimizer().optimize([stmt])

    assert stmt.expression is expr


def test_타입_불일치_연산은_접지_않고_그대로_둔다(mocker):
    # 3 - "hello" -> 실행 시 에러가 나야 하므로 폴딩하지 않는다
    expr = mocker.Mock(
        spec=Binary,
        left=mocker.Mock(spec=Literal, value=3.0),
        operator=make_operator_token(TokenType.MINUS, "-"),
        right=mocker.Mock(spec=Literal, value="hello"),
    )
    stmt = mocker.Mock(spec=ExpressionStmt, expression=expr)

    Optimizer().optimize([stmt])

    assert stmt.expression is expr


def test_var_stmt의_초기화식도_접힌다(mocker):
    expr = mocker.Mock(
        spec=Binary,
        left=mocker.Mock(spec=Literal, value=1.0),
        operator=make_operator_token(TokenType.PLUS, "+"),
        right=mocker.Mock(spec=Literal, value=2.0),
    )
    # Mock(name=...) 는 mock 자체의 표시 이름으로 예약된 인자라 필드로 못 쓴다.
    # 생성 후 속성으로 직접 지정한다.
    stmt = mocker.Mock(spec=VarStmt, initializer=expr)
    stmt.name = make_identifier_token("a")

    Optimizer().optimize([stmt])

    assert stmt.initializer == Literal(3.0)


def test_if문의_조건식과_양쪽_분기_모두_최적화된다(mocker):
    condition = mocker.Mock(
        spec=Binary,
        left=mocker.Mock(spec=Literal, value=1.0),
        operator=make_operator_token(TokenType.LESS, "<"),
        right=mocker.Mock(spec=Literal, value=2.0),
    )
    then_expr = mocker.Mock(
        spec=Binary,
        left=mocker.Mock(spec=Literal, value=1.0),
        operator=make_operator_token(TokenType.PLUS, "+"),
        right=mocker.Mock(spec=Literal, value=1.0),
    )
    else_expr = mocker.Mock(
        spec=Binary,
        left=mocker.Mock(spec=Literal, value=2.0),
        operator=make_operator_token(TokenType.PLUS, "+"),
        right=mocker.Mock(spec=Literal, value=2.0),
    )
    if_stmt = mocker.Mock(
        spec=IfStmt,
        condition=condition,
        then_branch=mocker.Mock(spec=ExpressionStmt, expression=then_expr),
        else_branch=mocker.Mock(spec=ExpressionStmt, expression=else_expr),
    )

    Optimizer().optimize([if_stmt])

    assert if_stmt.condition == Literal(True)
    assert if_stmt.then_branch.expression == Literal(2.0)
    assert if_stmt.else_branch.expression == Literal(4.0)


def test_logical_연산은_자식은_최적화되지만_자체는_접히지_않는다(mocker):
    # (1 + 1) 그리고 (2 + 2) -> 자식은 각각 리터럴로 접히지만 Logical 자체는 유지
    left = mocker.Mock(
        spec=Binary,
        left=mocker.Mock(spec=Literal, value=1.0),
        operator=make_operator_token(TokenType.PLUS, "+"),
        right=mocker.Mock(spec=Literal, value=1.0),
    )
    right = mocker.Mock(
        spec=Binary,
        left=mocker.Mock(spec=Literal, value=2.0),
        operator=make_operator_token(TokenType.PLUS, "+"),
        right=mocker.Mock(spec=Literal, value=2.0),
    )
    logical = mocker.Mock(
        spec=Logical, left=left, operator=make_operator_token(TokenType.AND, "그리고"), right=right
    )
    stmt = mocker.Mock(spec=PrintStmt, expression=logical)

    Optimizer().optimize([stmt])

    assert isinstance(stmt.expression, Logical)
    assert stmt.expression.left == Literal(2.0)
    assert stmt.expression.right == Literal(4.0)


def test_변수를_포함한_괄호는_풀리지_않고_그대로_유지된다(mocker):
    variable = mocker.Mock(spec=Variable)
    grouping = mocker.Mock(spec=Grouping, expression=variable)
    stmt = mocker.Mock(spec=ExpressionStmt, expression=grouping)

    Optimizer().optimize([stmt])

    assert stmt.expression is grouping
    assert stmt.expression.expression is variable


def test_변수에_대한_단항연산은_접히지_않는다(mocker):
    variable = mocker.Mock(spec=Variable)
    expr = mocker.Mock(spec=Unary, operator=make_operator_token(TokenType.MINUS, "-"), right=variable)
    stmt = mocker.Mock(spec=ExpressionStmt, expression=expr)

    Optimizer().optimize([stmt])

    assert stmt.expression is expr


def test_문자열에_단항_마이너스는_접히지_않는다(mocker):
    # -"hello" -> 실행 시 에러가 나야 하므로 폴딩하지 않는다
    right = mocker.Mock(spec=Literal, value="hello")
    expr = mocker.Mock(spec=Unary, operator=make_operator_token(TokenType.MINUS, "-"), right=right)
    stmt = mocker.Mock(spec=ExpressionStmt, expression=expr)

    Optimizer().optimize([stmt])

    assert stmt.expression is expr


def test_타입이_달라도_동등비교는_접힌다(mocker):
    equal_expr = mocker.Mock(
        spec=Binary,
        left=mocker.Mock(spec=Literal, value=1.0),
        operator=make_operator_token(TokenType.EQUAL_EQUAL, "=="),
        right=mocker.Mock(spec=Literal, value="1"),
    )
    not_equal_expr = mocker.Mock(
        spec=Binary,
        left=mocker.Mock(spec=Literal, value=1.0),
        operator=make_operator_token(TokenType.BANG_EQUAL, "!="),
        right=mocker.Mock(spec=Literal, value="1"),
    )

    stmt1 = mocker.Mock(spec=ExpressionStmt, expression=equal_expr)
    stmt2 = mocker.Mock(spec=ExpressionStmt, expression=not_equal_expr)
    Optimizer().optimize([stmt1, stmt2])

    assert stmt1.expression == Literal(False)
    assert stmt2.expression == Literal(True)


def test_숫자가_아니면_PLUS도_접지_않는다(mocker):
    # 1 + "a" -> 실행 시 에러가 나야 하므로 폴딩하지 않는다
    expr = mocker.Mock(
        spec=Binary,
        left=mocker.Mock(spec=Literal, value=1.0),
        operator=make_operator_token(TokenType.PLUS, "+"),
        right=mocker.Mock(spec=Literal, value="a"),
    )
    stmt = mocker.Mock(spec=ExpressionStmt, expression=expr)

    Optimizer().optimize([stmt])

    assert stmt.expression is expr


def test_지원하지_않는_이항연산자는_접지_않고_그대로_둔다(mocker):
    # Binary 노드에 AND 가 오는 일은 실제 문법상 없지만(그리고/또는은 Logical),
    # _fold_binary 의 방어적 fallback 분기를 검증한다.
    expr = mocker.Mock(
        spec=Binary,
        left=mocker.Mock(spec=Literal, value=1.0),
        operator=make_operator_token(TokenType.AND, "그리고"),
        right=mocker.Mock(spec=Literal, value=2.0),
    )
    stmt = mocker.Mock(spec=ExpressionStmt, expression=expr)

    Optimizer().optimize([stmt])

    assert stmt.expression is expr


@pytest.mark.parametrize(
    "op_type, op_lexeme, left, right, expected",
    [
        (TokenType.MINUS, "-", 5.0, 2.0, 3.0),
        (TokenType.STAR, "*", 3.0, 4.0, 12.0),
        (TokenType.SLASH, "/", 6.0, 2.0, 3.0),
        (TokenType.GREATER, ">", 3.0, 2.0, True),
        (TokenType.GREATER_EQUAL, ">=", 2.0, 2.0, True),
        (TokenType.LESS, "<", 1.0, 2.0, True),
        (TokenType.LESS_EQUAL, "<=", 2.0, 2.0, True),
    ],
)
def test_숫자_연산자들이_리터럴로_접힌다(mocker, op_type, op_lexeme, left, right, expected):
    expr = mocker.Mock(
        spec=Binary,
        left=mocker.Mock(spec=Literal, value=left),
        operator=make_operator_token(op_type, op_lexeme),
        right=mocker.Mock(spec=Literal, value=right),
    )
    stmt = mocker.Mock(spec=ExpressionStmt, expression=expr)

    Optimizer().optimize([stmt])

    assert stmt.expression == Literal(expected)


def test_bang은_None을_참으로_취급해서_접는다(mocker):
    # !null -> is_truthy(None) == False -> not False == True
    right = mocker.Mock(spec=Literal, value=None)
    expr = mocker.Mock(spec=Unary, operator=make_operator_token(TokenType.BANG, "!"), right=right)
    stmt = mocker.Mock(spec=ExpressionStmt, expression=expr)

    Optimizer().optimize([stmt])

    assert stmt.expression == Literal(True)


def test_bang은_불리언이_아닌_값도_참으로_취급해서_접는다(mocker):
    # !"hi" -> is_truthy("hi") == True -> not True == False
    right = mocker.Mock(spec=Literal, value="hi")
    expr = mocker.Mock(spec=Unary, operator=make_operator_token(TokenType.BANG, "!"), right=right)
    stmt = mocker.Mock(spec=ExpressionStmt, expression=expr)

    Optimizer().optimize([stmt])

    assert stmt.expression == Literal(False)


def test_array_리터럴의_size와_인덱스_표현식도_접힌다(mocker):
    size_expr = mocker.Mock(
        spec=Binary,
        left=mocker.Mock(spec=Literal, value=1.0),
        operator=make_operator_token(TokenType.PLUS, "+"),
        right=mocker.Mock(spec=Literal, value=2.0),
    )
    array_literal = mocker.Mock(spec=ArrayLiteral, size=size_expr, line=1)
    index_expr = mocker.Mock(
        spec=Binary,
        left=mocker.Mock(spec=Literal, value=0.0),
        operator=make_operator_token(TokenType.PLUS, "+"),
        right=mocker.Mock(spec=Literal, value=1.0),
    )
    index_get = mocker.Mock(spec=IndexGet, target=array_literal, index=index_expr, line=1)
    stmt = mocker.Mock(spec=ExpressionStmt, expression=index_get)

    Optimizer().optimize([stmt])

    assert array_literal.size == Literal(3.0)
    assert index_get.index == Literal(1.0)
