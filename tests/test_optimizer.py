from codefab.array_nodes import ArrayLiteral, IndexGet
from codefab.ast_nodes import (
    Binary,
    ExpressionStmt,
    Grouping,
    Literal,
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


def test_리터럴_상수_이항연산은_하나의_리터럴로_접힌다():
    # 1 + 2
    expr = Binary(Literal(1.0), make_operator_token(TokenType.PLUS, "+"), Literal(2.0))
    stmt = ExpressionStmt(expr)

    Optimizer().optimize([stmt])

    assert stmt.expression == Literal(3.0)


def test_문자열_리터럴_덧셈도_접힌다():
    expr = Binary(Literal("a"), make_operator_token(TokenType.PLUS, "+"), Literal("b"))
    stmt = ExpressionStmt(expr)

    Optimizer().optimize([stmt])

    assert stmt.expression == Literal("ab")


def test_중첩된_상수_연산은_전부_접혀서_하나의_리터럴이_된다():
    # (1 - 2 * 3) 같은 pdf 예시 축소판: 1 + 2 * 3
    inner = Binary(Literal(2.0), make_operator_token(TokenType.STAR, "*"), Literal(3.0))
    outer = Binary(Literal(1.0), make_operator_token(TokenType.PLUS, "+"), inner)
    stmt = ExpressionStmt(outer)

    Optimizer().optimize([stmt])

    assert stmt.expression == Literal(7.0)


def test_괄호로_감싼_상수도_접힌다():
    # (1 + 2)
    inner = Binary(Literal(1.0), make_operator_token(TokenType.PLUS, "+"), Literal(2.0))
    stmt = ExpressionStmt(Grouping(inner))

    Optimizer().optimize([stmt])

    assert stmt.expression == Literal(3.0)


def test_단항_마이너스_상수는_접힌다():
    expr = Unary(make_operator_token(TokenType.MINUS, "-"), Literal(3.0))
    stmt = ExpressionStmt(expr)

    Optimizer().optimize([stmt])

    assert stmt.expression == Literal(-3.0)


def test_단항_bang_상수는_접힌다():
    expr = Unary(make_operator_token(TokenType.BANG, "!"), Literal(False))
    stmt = ExpressionStmt(expr)

    Optimizer().optimize([stmt])

    assert stmt.expression == Literal(True)


def test_변수가_포함된_연산은_접히지_않는다():
    variable = Variable(make_identifier_token("a"))
    expr = Binary(variable, make_operator_token(TokenType.PLUS, "+"), Literal(1.0))
    stmt = ExpressionStmt(expr)

    Optimizer().optimize([stmt])

    assert stmt.expression is expr
    assert stmt.expression.left is variable


def test_0으로_나누는_상수연산은_접지_않고_그대로_둔다():
    expr = Binary(Literal(1.0), make_operator_token(TokenType.SLASH, "/"), Literal(0.0))
    stmt = ExpressionStmt(expr)

    Optimizer().optimize([stmt])

    assert stmt.expression is expr


def test_타입_불일치_연산은_접지_않고_그대로_둔다():
    # 3 - "hello" -> 실행 시 에러가 나야 하므로 폴딩하지 않는다
    expr = Binary(Literal(3.0), make_operator_token(TokenType.MINUS, "-"), Literal("hello"))
    stmt = ExpressionStmt(expr)

    Optimizer().optimize([stmt])

    assert stmt.expression is expr


def test_var_stmt의_초기화식도_접힌다():
    expr = Binary(Literal(1.0), make_operator_token(TokenType.PLUS, "+"), Literal(2.0))
    stmt = VarStmt(make_identifier_token("a"), expr)

    Optimizer().optimize([stmt])

    assert stmt.initializer == Literal(3.0)


def test_array_리터럴의_size와_인덱스_표현식도_접힌다():
    size_expr = Binary(Literal(1.0), make_operator_token(TokenType.PLUS, "+"), Literal(2.0))
    array_literal = ArrayLiteral(size_expr, line=1)
    index_expr = Binary(Literal(0.0), make_operator_token(TokenType.PLUS, "+"), Literal(1.0))
    index_get = IndexGet(array_literal, index_expr, line=1)
    stmt = ExpressionStmt(index_get)

    Optimizer().optimize([stmt])

    assert array_literal.size == Literal(3.0)
    assert index_get.index == Literal(1.0)
