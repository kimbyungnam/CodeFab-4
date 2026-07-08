from codefab.ast_nodes import (
    Assign,
    Binary,
    BlockStmt,
    ExpressionStmt,
    Literal,
    PrintStmt,
    Variable,
    VarStmt,
)
from codefab.executor_unit import Environment
from codefab.resolver import OptimizedExecutorUnit, Resolver
from codefab.tokens import Token, TokenType


def make_identifier_token(lexeme: str, line: int = 1) -> Token:
    return Token(type=TokenType.IDENTIFIER, lexeme=lexeme, literal=None, line=line)


def test_distance가_없으면_기존_동적_조회로_동작한다(capsys):
    # var a = 1; print a;  (전역 변수라 distance 가 안 붙는다)
    var_stmt = VarStmt(make_identifier_token("a"), Literal(1.0))
    print_stmt = PrintStmt(Variable(make_identifier_token("a")))

    Resolver().resolve([var_stmt, print_stmt])
    OptimizedExecutorUnit().execute([var_stmt, print_stmt])

    assert capsys.readouterr().out.splitlines() == ["1"]


def test_distance가_있으면_스코프를_거슬러_올라가지_않고_바로_값을_읽는다(
    mocker, capsys
):
    # { var a = 5; print a; }
    var_stmt = VarStmt(make_identifier_token("a"), Literal(5.0))
    variable_a = Variable(make_identifier_token("a"))
    block = BlockStmt([var_stmt, PrintStmt(variable_a)])

    Resolver().resolve([block])
    assert variable_a.distance == 0

    get_spy = mocker.spy(Environment, "get")
    OptimizedExecutorUnit().execute([block])

    assert capsys.readouterr().out.splitlines() == ["5"]
    get_spy.assert_not_called()  # 동적 조회(Environment.get)를 타지 않았어야 한다


def test_distance가_있는_대입도_스코프를_거슬러_올라가지_않는다(mocker, capsys):
    # { var a = 1; a = a + 1; print a; }
    var_stmt = VarStmt(make_identifier_token("a"), Literal(1.0))
    assign = Assign(
        make_identifier_token("a"),
        Binary(
            Variable(make_identifier_token("a")),
            Token(TokenType.PLUS, "+", literal=None, line=1),
            Literal(1.0),
        ),
    )
    block = BlockStmt(
        [
            var_stmt,
            ExpressionStmt(assign),
            PrintStmt(Variable(make_identifier_token("a"))),
        ]
    )

    Resolver().resolve([block])
    assert assign.distance == 0

    assign_spy = mocker.spy(Environment, "assign")
    OptimizedExecutorUnit().execute([block])

    assert capsys.readouterr().out.splitlines() == ["2"]
    assign_spy.assert_not_called()


def test_중첩_스코프에서도_결과값이_기존_ExecutorUnit과_동일하다(capsys):
    # { var a = 1; { var b = 2; print a + b; } }
    inner_ref_a = Variable(make_identifier_token("a"))
    inner_ref_b = Variable(make_identifier_token("b"))
    inner_block = BlockStmt(
        [
            VarStmt(make_identifier_token("b"), Literal(2.0)),
            PrintStmt(
                Binary(
                    inner_ref_a,
                    Token(TokenType.PLUS, "+", literal=None, line=1),
                    inner_ref_b,
                )
            ),
        ]
    )
    outer_block = BlockStmt(
        [VarStmt(make_identifier_token("a"), Literal(1.0)), inner_block]
    )

    Resolver().resolve([outer_block])
    assert inner_ref_a.distance == 1
    assert inner_ref_b.distance == 0

    OptimizedExecutorUnit().execute([outer_block])

    assert capsys.readouterr().out.splitlines() == ["3"]
