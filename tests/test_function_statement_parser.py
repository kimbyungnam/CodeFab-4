import pytest

from codefab.assembler.function_statement_parser import FunctionStatementParser
from codefab.ast import (
    Assign,
    Binary,
    Call,
    ExpressionStmt,
    FunctionStmt,
    IfStmt,
    Literal,
    ReturnStmt,
    Variable,
)
from codefab.errors import ParseError
from codefab.tokens import Token, TokenType


def _tok(token_type, lexeme, literal=None, line=1):
    return Token(token_type, lexeme, literal=literal, line=line)


def _eof(line=1):
    return _tok(TokenType.EOF, "", line=line)


def test_함수_선언은_FunctionStmt로_파싱된다():
    # 함수 add(a, b) { 반환 a + b; }
    tokens = [
        _tok(TokenType.FUN, "함수"),
        _tok(TokenType.IDENTIFIER, "add"),
        _tok(TokenType.LEFT_PAREN, "("),
        _tok(TokenType.IDENTIFIER, "a"),
        _tok(TokenType.COMMA, ","),
        _tok(TokenType.IDENTIFIER, "b"),
        _tok(TokenType.RIGHT_PAREN, ")"),
        _tok(TokenType.LEFT_BRACE, "{"),
        _tok(TokenType.RETURN, "반환"),
        _tok(TokenType.IDENTIFIER, "a"),
        _tok(TokenType.PLUS, "+"),
        _tok(TokenType.IDENTIFIER, "b"),
        _tok(TokenType.SEMICOLON, ";"),
        _tok(TokenType.RIGHT_BRACE, "}"),
        _eof(),
    ]

    statements = FunctionStatementParser(tokens).parse()

    assert len(statements) == 1
    stmt = statements[0]
    assert isinstance(stmt, FunctionStmt)
    assert stmt.name.lexeme == "add"
    assert [p.lexeme for p in stmt.params] == ["a", "b"]
    assert len(stmt.body) == 1
    assert isinstance(stmt.body[0], ReturnStmt)
    assert isinstance(stmt.body[0].value, Binary)


def test_파라미터가_없는_함수_선언도_파싱된다():
    # 함수 noop() { 반환; }
    tokens = [
        _tok(TokenType.FUN, "함수"),
        _tok(TokenType.IDENTIFIER, "noop"),
        _tok(TokenType.LEFT_PAREN, "("),
        _tok(TokenType.RIGHT_PAREN, ")"),
        _tok(TokenType.LEFT_BRACE, "{"),
        _tok(TokenType.RETURN, "반환"),
        _tok(TokenType.SEMICOLON, ";"),
        _tok(TokenType.RIGHT_BRACE, "}"),
        _eof(),
    ]

    stmt = FunctionStatementParser(tokens).parse()[0]

    assert isinstance(stmt, FunctionStmt)
    assert stmt.params == []
    assert isinstance(stmt.body[0], ReturnStmt)
    assert stmt.body[0].value is None


def test_반환값이_있는_반환문은_ReturnStmt로_파싱된다():
    # 반환 5;
    tokens = [
        _tok(TokenType.RETURN, "반환"),
        _tok(TokenType.NUMBER, "5", literal=5.0),
        _tok(TokenType.SEMICOLON, ";"),
        _eof(),
    ]

    stmt = FunctionStatementParser(tokens).parse()[0]

    assert isinstance(stmt, ReturnStmt)
    assert stmt.value == Literal(5.0)
    assert stmt.keyword.lexeme == "반환"


def test_반환값이_없는_반환문은_value가_None이다():
    # 반환;
    tokens = [
        _tok(TokenType.RETURN, "반환"),
        _tok(TokenType.SEMICOLON, ";"),
        _eof(),
    ]

    stmt = FunctionStatementParser(tokens).parse()[0]

    assert isinstance(stmt, ReturnStmt)
    assert stmt.value is None


def test_함수_호출_표현식은_Call로_파싱된다():
    # add(3, 7);
    tokens = [
        _tok(TokenType.IDENTIFIER, "add"),
        _tok(TokenType.LEFT_PAREN, "("),
        _tok(TokenType.NUMBER, "3", literal=3.0),
        _tok(TokenType.COMMA, ","),
        _tok(TokenType.NUMBER, "7", literal=7.0),
        _tok(TokenType.RIGHT_PAREN, ")"),
        _tok(TokenType.SEMICOLON, ";"),
        _eof(),
    ]

    stmt = FunctionStatementParser(tokens).parse()[0]

    assert isinstance(stmt, ExpressionStmt)
    call = stmt.expression
    assert isinstance(call, Call)
    assert isinstance(call.callee, Variable)
    assert call.callee.name.lexeme == "add"
    assert call.arguments == [Literal(3.0), Literal(7.0)]


def test_인자가_없는_함수_호출도_파싱된다():
    # noop();
    tokens = [
        _tok(TokenType.IDENTIFIER, "noop"),
        _tok(TokenType.LEFT_PAREN, "("),
        _tok(TokenType.RIGHT_PAREN, ")"),
        _tok(TokenType.SEMICOLON, ";"),
        _eof(),
    ]

    stmt = FunctionStatementParser(tokens).parse()[0]

    assert isinstance(stmt.expression, Call)
    assert stmt.expression.arguments == []


def test_함수_호출_결과를_대입할_수_있다():
    # 변수 ret = add(3, 7);
    tokens = [
        _tok(TokenType.VAR, "변수"),
        _tok(TokenType.IDENTIFIER, "ret"),
        _tok(TokenType.EQUAL, "="),
        _tok(TokenType.IDENTIFIER, "add"),
        _tok(TokenType.LEFT_PAREN, "("),
        _tok(TokenType.NUMBER, "3", literal=3.0),
        _tok(TokenType.COMMA, ","),
        _tok(TokenType.NUMBER, "7", literal=7.0),
        _tok(TokenType.RIGHT_PAREN, ")"),
        _tok(TokenType.SEMICOLON, ";"),
        _eof(),
    ]

    stmt = FunctionStatementParser(tokens).parse()[0]

    assert isinstance(stmt.initializer, Call)


def test_연쇄_호출도_파싱된다():
    # make_adder()(1);
    tokens = [
        _tok(TokenType.IDENTIFIER, "make_adder"),
        _tok(TokenType.LEFT_PAREN, "("),
        _tok(TokenType.RIGHT_PAREN, ")"),
        _tok(TokenType.LEFT_PAREN, "("),
        _tok(TokenType.NUMBER, "1", literal=1.0),
        _tok(TokenType.RIGHT_PAREN, ")"),
        _tok(TokenType.SEMICOLON, ";"),
        _eof(),
    ]

    call = FunctionStatementParser(tokens).parse()[0].expression

    assert isinstance(call, Call)
    assert call.arguments == [Literal(1.0)]
    assert isinstance(call.callee, Call)
    assert call.callee.arguments == []


def test_함수가_아닌_기존_문장도_여전히_파싱된다():
    # 만약 (x > 0) y = 1;
    tokens = [
        _tok(TokenType.IF, "만약"),
        _tok(TokenType.LEFT_PAREN, "("),
        _tok(TokenType.IDENTIFIER, "x"),
        _tok(TokenType.GREATER, ">"),
        _tok(TokenType.NUMBER, "0", literal=0.0),
        _tok(TokenType.RIGHT_PAREN, ")"),
        _tok(TokenType.IDENTIFIER, "y"),
        _tok(TokenType.EQUAL, "="),
        _tok(TokenType.NUMBER, "1", literal=1.0),
        _tok(TokenType.SEMICOLON, ";"),
        _eof(),
    ]

    stmt = FunctionStatementParser(tokens).parse()[0]

    assert isinstance(stmt, IfStmt)
    assert isinstance(stmt.then_branch.expression, Assign)


def test_함수_이름_누락시_에러():
    # 함수 (a) { 반환 a; }
    tokens = [
        _tok(TokenType.FUN, "함수"),
        _tok(TokenType.LEFT_PAREN, "("),
        _tok(TokenType.IDENTIFIER, "a"),
        _tok(TokenType.RIGHT_PAREN, ")"),
        _tok(TokenType.LEFT_BRACE, "{"),
        _tok(TokenType.RETURN, "반환"),
        _tok(TokenType.IDENTIFIER, "a"),
        _tok(TokenType.SEMICOLON, ";"),
        _tok(TokenType.RIGHT_BRACE, "}"),
        _eof(),
    ]

    with pytest.raises(ParseError, match="함수 이름이 필요합니다."):
        FunctionStatementParser(tokens).parse()


def test_파라미터_이름_자리에_잘못된_토큰이_오면_에러():
    # 함수 foo(1) { 반환 1; }
    tokens = [
        _tok(TokenType.FUN, "함수"),
        _tok(TokenType.IDENTIFIER, "foo"),
        _tok(TokenType.LEFT_PAREN, "("),
        _tok(TokenType.NUMBER, "1", literal=1.0),
        _tok(TokenType.RIGHT_PAREN, ")"),
        _tok(TokenType.LEFT_BRACE, "{"),
        _tok(TokenType.RETURN, "반환"),
        _tok(TokenType.NUMBER, "1", literal=1.0),
        _tok(TokenType.SEMICOLON, ";"),
        _tok(TokenType.RIGHT_BRACE, "}"),
        _eof(),
    ]

    with pytest.raises(ParseError, match="파라미터 이름이 필요합니다."):
        FunctionStatementParser(tokens).parse()


def test_함수_본문이_중괄호로_시작하지_않으면_에러():
    # 함수 foo() 반환 1;
    tokens = [
        _tok(TokenType.FUN, "함수"),
        _tok(TokenType.IDENTIFIER, "foo"),
        _tok(TokenType.LEFT_PAREN, "("),
        _tok(TokenType.RIGHT_PAREN, ")"),
        _tok(TokenType.RETURN, "반환"),
        _tok(TokenType.NUMBER, "1", literal=1.0),
        _tok(TokenType.SEMICOLON, ";"),
        _eof(),
    ]

    with pytest.raises(ParseError, match="함수 본문은 '\\{'로 시작해야 합니다."):
        FunctionStatementParser(tokens).parse()


def test_호출_인자_목록이_닫히지_않으면_에러():
    # add(1, 2;
    tokens = [
        _tok(TokenType.IDENTIFIER, "add"),
        _tok(TokenType.LEFT_PAREN, "("),
        _tok(TokenType.NUMBER, "1", literal=1.0),
        _tok(TokenType.COMMA, ","),
        _tok(TokenType.NUMBER, "2", literal=2.0),
        _tok(TokenType.SEMICOLON, ";"),
        _eof(),
    ]

    with pytest.raises(ParseError, match="인자 목록 뒤에는 '\\)'가 필요합니다."):
        FunctionStatementParser(tokens).parse()
