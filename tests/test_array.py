import pytest

from codefab.array_nodes import ArrayLiteral, IndexGet, IndexSet
from codefab.assembler.expression_parser import ExpressionParser
from codefab.ast_nodes import Literal, Variable, VarStmt
from codefab.checker import Checker
from codefab.error import (
    ArrayIndexNotNumberError,
    ArrayIndexOutOfRangeError,
    ArraySizeNotNumberError,
    NotIndexableError,
    ParseError,
    SelfReferenceInInitializerError,
)
from codefab.executor_unit import ExecutorUnit
from codefab.tokens import Token, TokenType


def make_identifier_token(lexeme: str, line: int = 1) -> Token:
    return Token(type=TokenType.IDENTIFIER, lexeme=lexeme, literal=None, line=line)


def make_array_token(lexeme: str = "Array", line: int = 1) -> Token:
    return Token(type=TokenType.ARRAY, lexeme=lexeme, literal=None, line=line)


@pytest.fixture
def executor() -> ExecutorUnit:
    return ExecutorUnit()


def evaluate(executor: ExecutorUnit, expression):
    return executor._evaluate_expr(expression)  # noqa: SLF001 — 표현식 평가만 단독으로 검증


# ---------------- ExpressionParser ----------------


def test_array_리터럴은_ArrayLiteral로_파싱된다():
    # Array(3)
    tokens = [
        make_array_token(),
        Token(TokenType.LEFT_PAREN, "(", literal=None, line=1),
        Token(TokenType.NUMBER, "3", line=1, literal=3.0),
        Token(TokenType.RIGHT_PAREN, ")", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert expression == ArrayLiteral(Literal(3.0), line=1)


def test_한글_배열_키워드도_ArrayLiteral로_파싱된다():
    # 배열(3)
    tokens = [
        make_array_token("배열"),
        Token(TokenType.LEFT_PAREN, "(", literal=None, line=1),
        Token(TokenType.NUMBER, "3", line=1, literal=3.0),
        Token(TokenType.RIGHT_PAREN, ")", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert expression == ArrayLiteral(Literal(3.0), line=1)


def test_인덱스_읽기는_IndexGet으로_파싱된다():
    # arr[0]
    tokens = [
        make_identifier_token("arr"),
        Token(TokenType.LEFT_BRACKET, "[", literal=None, line=1),
        Token(TokenType.NUMBER, "0", line=1, literal=0.0),
        Token(TokenType.RIGHT_BRACKET, "]", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, IndexGet)
    assert expression.target == Variable(make_identifier_token("arr"))
    assert expression.index == Literal(0.0)


def test_인덱스_쓰기는_IndexSet으로_파싱된다():
    # arr[0] = 10
    tokens = [
        make_identifier_token("arr"),
        Token(TokenType.LEFT_BRACKET, "[", literal=None, line=1),
        Token(TokenType.NUMBER, "0", line=1, literal=0.0),
        Token(TokenType.RIGHT_BRACKET, "]", literal=None, line=1),
        Token(TokenType.EQUAL, "=", literal=None, line=1),
        Token(TokenType.NUMBER, "10", line=1, literal=10.0),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, IndexSet)
    assert expression.index == Literal(0.0)
    assert expression.value == Literal(10.0)


def test_닫는_대괄호가_없으면_ParseError():
    # arr[0
    tokens = [
        make_identifier_token("arr"),
        Token(TokenType.LEFT_BRACKET, "[", literal=None, line=1),
        Token(TokenType.NUMBER, "0", line=1, literal=0.0),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    with pytest.raises(ParseError):
        ExpressionParser(tokens).parse()


def test_array_뒤에_여는_괄호가_없으면_ParseError():
    # Array 3)
    tokens = [
        make_array_token(),
        Token(TokenType.NUMBER, "3", line=1, literal=3.0),
        Token(TokenType.RIGHT_PAREN, ")", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    with pytest.raises(ParseError):
        ExpressionParser(tokens).parse()


# ---------------- Checker ----------------


def test_checker는_array_리터럴의_size를_방문한다():
    initializing_self_ref = ArrayLiteral(Variable(make_identifier_token("arr")), line=1)
    var_stmt = VarStmt(make_identifier_token("arr"), initializing_self_ref)

    with pytest.raises(SelfReferenceInInitializerError):
        Checker().resolve([var_stmt])


def test_checker는_index_get의_target과_index를_방문한다():
    self_ref = IndexGet(
        target=Variable(make_identifier_token("arr")),
        index=Literal(0.0),
        line=1,
    )
    var_stmt = VarStmt(make_identifier_token("arr"), self_ref)

    with pytest.raises(SelfReferenceInInitializerError):
        Checker().resolve([var_stmt])


def test_checker는_index_set의_target_index_value를_방문한다():
    self_ref = IndexSet(
        target=Variable(make_identifier_token("other")),
        index=Literal(0.0),
        value=Variable(make_identifier_token("arr")),
        line=1,
    )
    var_stmt = VarStmt(make_identifier_token("arr"), self_ref)

    with pytest.raises(SelfReferenceInInitializerError):
        Checker().resolve([var_stmt])


# ---------------- ExecutorUnit ----------------


def test_array는_지정한_크기만큼_None으로_채워진_리스트를_생성한다(executor):
    result = evaluate(executor, ArrayLiteral(Literal(3.0), line=1))

    assert result == [None, None, None]


def test_array_크기가_숫자가_아니면_런타임_오류(executor):
    with pytest.raises(ArraySizeNotNumberError):
        evaluate(executor, ArrayLiteral(Literal("hi"), line=1))


def test_인덱스로_읽고_쓸_수_있다(executor):
    array = evaluate(executor, ArrayLiteral(Literal(3.0), line=1))
    executor.environment.define("arr", array)
    arr_var = Variable(make_identifier_token("arr"))

    evaluate(
        executor,
        IndexSet(target=arr_var, index=Literal(1.0), value=Literal(20.0), line=1),
    )
    value = evaluate(executor, IndexGet(target=arr_var, index=Literal(1.0), line=1))

    assert value == 20.0
    assert array == [None, 20.0, None]


def test_범위를_벗어난_인덱스는_런타임_오류(executor):
    with pytest.raises(ArrayIndexOutOfRangeError):
        evaluate(
            executor,
            IndexGet(
                target=ArrayLiteral(Literal(3.0), line=1), index=Literal(5.0), line=1
            ),
        )


def test_음수_인덱스는_런타임_오류(executor):
    with pytest.raises(ArrayIndexOutOfRangeError):
        evaluate(
            executor,
            IndexGet(
                target=ArrayLiteral(Literal(3.0), line=1), index=Literal(-1.0), line=1
            ),
        )


def test_인덱스가_숫자가_아니면_런타임_오류(executor):
    with pytest.raises(ArrayIndexNotNumberError):
        evaluate(
            executor,
            IndexGet(
                target=ArrayLiteral(Literal(3.0), line=1),
                index=Literal("hello"),
                line=1,
            ),
        )


def test_배열이_아닌_대상에_인덱스_접근시_런타임_오류(executor):
    with pytest.raises(NotIndexableError):
        evaluate(executor, IndexGet(target=Literal(10.0), index=Literal(0.0), line=1))
