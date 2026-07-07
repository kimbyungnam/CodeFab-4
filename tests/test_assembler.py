import pytest

from codefab.assembler.assembler import Assembler
from codefab.assembler.errors import ParseError
from codefab.ast_nodes import IfStmt, Literal, PrintStmt, VarStmt


def test_assemble_empty_source_returns_empty_list():
    assert Assembler("").assemble() == []


def test_assemble_single_var_declaration():
    statements = Assembler("var a = 3;").assemble()

    assert len(statements) == 1
    stmt = statements[0]
    assert isinstance(stmt, VarStmt)
    assert stmt.name.lexeme == "a"
    assert stmt.initializer == Literal(3.0)


def test_assemble_multiple_statements_in_order():
    statements = Assembler("var a = 1; print a;").assemble()

    assert len(statements) == 2
    assert isinstance(statements[0], VarStmt)
    assert isinstance(statements[1], PrintStmt)


def test_assemble_if_statement_without_else():
    statements = Assembler("if (a > 0) print a;").assemble()

    assert len(statements) == 1
    stmt = statements[0]
    assert isinstance(stmt, IfStmt)
    assert isinstance(stmt.then_branch, PrintStmt)
    assert stmt.else_branch is None


def test_assemble_korean_var_and_print_declaration():
    # docs/language.md 문법 정의: VAR/PRINT 의 표면 lexeme 은 "변수"/"출력"
    statements = Assembler("변수 a = 3; 출력 a;").assemble()

    assert len(statements) == 2
    var_stmt, print_stmt = statements
    assert isinstance(var_stmt, VarStmt)
    assert var_stmt.name.lexeme == "a"
    assert var_stmt.initializer == Literal(3.0)
    assert isinstance(print_stmt, PrintStmt)


def test_assemble_propagates_parse_error_without_swallowing():
    # var 뒤에 식별자가 없어 StatementParser 가 ParseError 를 던진다.
    with pytest.raises(ParseError):
        Assembler("var = 3;").assemble()
