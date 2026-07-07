from codefab.assembler.expr import Assign, Binary, Literal, Variable
from codefab.assembler.statement_parser import StatementParser
from codefab.ast_nodes import (
    BlockStmt,
    ExpressionStmt,
    ForStmt,
    IfStmt,
    PrintStmt,
    VarStmt,
)
from codefab.tokens import Token, TokenType


def test_if_stmt_without_else_is_parsed_as_if_stmt():
    # 만약 (x > 0) y = 1;
    tokens = [
        Token(TokenType.IF, "만약", literal=None, line=1),
        Token(TokenType.LEFT_PAREN, "(", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "x", literal=None, line=1),
        Token(TokenType.GREATER, ">", literal=None, line=1),
        Token(TokenType.NUMBER, "0", literal=0.0, line=1),
        Token(TokenType.RIGHT_PAREN, ")", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "y", literal=None, line=2),
        Token(TokenType.EQUAL, "=", literal=None, line=2),
        Token(TokenType.NUMBER, "1", literal=1.0, line=2),
        Token(TokenType.SEMICOLON, ";", literal=None, line=2),
        Token(TokenType.EOF, "", literal=None, line=2),
    ]

    statements = StatementParser(tokens).parse()

    assert len(statements) == 1
    stmt = statements[0]
    assert isinstance(stmt, IfStmt)

    assert isinstance(stmt.condition, Binary)
    assert stmt.condition.operator.lexeme == ">"
    assert isinstance(stmt.condition.left, Variable)
    assert stmt.condition.left.name.lexeme == "x"
    assert stmt.condition.right == Literal(0.0)

    assert isinstance(stmt.then_branch, ExpressionStmt)
    assert isinstance(stmt.then_branch.expression, Assign)
    assert stmt.then_branch.expression.name.lexeme == "y"
    assert stmt.then_branch.expression.value == Literal(1.0)

    assert stmt.else_branch is None


def test_if_stmt_with_else_is_parsed_as_if_stmt():
    # 만약 (x > 0) y = 1; 아니면 y = 2;
    tokens = [
        Token(TokenType.IF, "만약", literal=None, line=1),
        Token(TokenType.LEFT_PAREN, "(", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "x", literal=None, line=1),
        Token(TokenType.GREATER, ">", literal=None, line=1),
        Token(TokenType.NUMBER, "0", literal=0.0, line=1),
        Token(TokenType.RIGHT_PAREN, ")", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "y", literal=None, line=1),
        Token(TokenType.EQUAL, "=", literal=None, line=1),
        Token(TokenType.NUMBER, "1", literal=1.0, line=1),
        Token(TokenType.SEMICOLON, ";", literal=None, line=1),
        Token(TokenType.ELSE, "아니면", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "y", literal=None, line=1),
        Token(TokenType.EQUAL, "=", literal=None, line=1),
        Token(TokenType.NUMBER, "2", literal=2.0, line=1),
        Token(TokenType.SEMICOLON, ";", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    stmt = StatementParser(tokens).parse()[0]

    assert isinstance(stmt, IfStmt)
    assert isinstance(stmt.then_branch, ExpressionStmt)
    assert isinstance(stmt.else_branch, ExpressionStmt)
    assert stmt.else_branch.expression.value == Literal(2.0)


def test_if_stmt_with_else_matches_language_md_example():
    # 만약 (x > 0) y = 1; 아니면 y = 2;
    tokens = [
        Token(TokenType.IF, "만약", literal=None, line=1),
        Token(TokenType.LEFT_PAREN, "(", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "x", literal=None, line=1),
        Token(TokenType.GREATER, ">", literal=None, line=1),
        Token(TokenType.NUMBER, "0", literal=0.0, line=1),
        Token(TokenType.RIGHT_PAREN, ")", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "y", literal=None, line=1),
        Token(TokenType.EQUAL, "=", literal=None, line=1),
        Token(TokenType.NUMBER, "1", literal=1.0, line=1),
        Token(TokenType.SEMICOLON, ";", literal=None, line=1),
        Token(TokenType.ELSE, "아니면", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "y", literal=None, line=1),
        Token(TokenType.EQUAL, "=", literal=None, line=1),
        Token(TokenType.NUMBER, "2", literal=2.0, line=1),
        Token(TokenType.SEMICOLON, ";", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    stmt = StatementParser(tokens).parse()[0]

    expected = IfStmt(
        condition=Binary(
            left=Variable(Token(TokenType.IDENTIFIER, "x", None, 1)),
            operator=Token(TokenType.GREATER, ">", None, 1),
            right=Literal(0.0),
        ),
        then_branch=ExpressionStmt(
            Assign(Token(TokenType.IDENTIFIER, "y", None, 1), Literal(1.0))
        ),
        else_branch=ExpressionStmt(
            Assign(Token(TokenType.IDENTIFIER, "y", None, 1), Literal(2.0))
        ),
    )

    assert stmt == expected


def test_block_stmt_groups_multiple_statements():
    # { x = 1; y = 2; }
    tokens = [
        Token(TokenType.LEFT_BRACE, "{", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "x", literal=None, line=1),
        Token(TokenType.EQUAL, "=", literal=None, line=1),
        Token(TokenType.NUMBER, "1", literal=1.0, line=1),
        Token(TokenType.SEMICOLON, ";", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "y", literal=None, line=1),
        Token(TokenType.EQUAL, "=", literal=None, line=1),
        Token(TokenType.NUMBER, "2", literal=2.0, line=1),
        Token(TokenType.SEMICOLON, ";", literal=None, line=1),
        Token(TokenType.RIGHT_BRACE, "}", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    stmt = StatementParser(tokens).parse()[0]

    assert isinstance(stmt, BlockStmt)
    assert len(stmt.statements) == 2
    assert all(isinstance(s, ExpressionStmt) for s in stmt.statements)


def test_print_stmt_is_parsed_as_print_stmt():
    # 출력 a;
    tokens = [
        Token(TokenType.PRINT, "출력", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "a", literal=None, line=1),
        Token(TokenType.SEMICOLON, ";", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    stmt = StatementParser(tokens).parse()[0]

    assert isinstance(stmt, PrintStmt)
    assert isinstance(stmt.expression, Variable)
    assert stmt.expression.name.lexeme == "a"


def test_for_stmt_is_parsed_as_for_stmt():
    # 반복 (변수 i = 0; i < 3; i = i + 1) { 출력 i; }
    tokens = [
        Token(TokenType.FOR, "반복", literal=None, line=1),
        Token(TokenType.LEFT_PAREN, "(", literal=None, line=1),
        Token(TokenType.VAR, "변수", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "i", literal=None, line=1),
        Token(TokenType.EQUAL, "=", literal=None, line=1),
        Token(TokenType.NUMBER, "0", literal=0.0, line=1),
        Token(TokenType.SEMICOLON, ";", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "i", literal=None, line=1),
        Token(TokenType.LESS, "<", literal=None, line=1),
        Token(TokenType.NUMBER, "3", literal=3.0, line=1),
        Token(TokenType.SEMICOLON, ";", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "i", literal=None, line=1),
        Token(TokenType.EQUAL, "=", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "i", literal=None, line=1),
        Token(TokenType.PLUS, "+", literal=None, line=1),
        Token(TokenType.NUMBER, "1", literal=1.0, line=1),
        Token(TokenType.RIGHT_PAREN, ")", literal=None, line=1),
        Token(TokenType.LEFT_BRACE, "{", literal=None, line=1),
        Token(TokenType.PRINT, "출력", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "i", literal=None, line=1),
        Token(TokenType.SEMICOLON, ";", literal=None, line=1),
        Token(TokenType.RIGHT_BRACE, "}", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    stmt = StatementParser(tokens).parse()[0]

    assert isinstance(stmt, ForStmt)
    assert isinstance(stmt.initializer, VarStmt)
    assert isinstance(stmt.condition, Binary)
    assert isinstance(stmt.increment, Assign)
    assert isinstance(stmt.body, BlockStmt)


def test_var_declaration_with_initializer_is_parsed_as_var_stmt():
    # 변수 x = 10;
    tokens = [
        Token(TokenType.VAR, "변수", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "x", literal=None, line=1),
        Token(TokenType.EQUAL, "=", literal=None, line=1),
        Token(TokenType.NUMBER, "10", literal=10.0, line=1),
        Token(TokenType.SEMICOLON, ";", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    statements = StatementParser(tokens).parse()

    assert len(statements) == 1
    stmt = statements[0]
    assert isinstance(stmt, VarStmt)
    assert stmt.name.lexeme == "x"
    assert stmt.initializer == Literal(10.0)
