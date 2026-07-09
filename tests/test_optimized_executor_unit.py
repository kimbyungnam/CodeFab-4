from codefab.ast import (
    Assign,
    Binary,
    BlockStmt,
    ExpressionStmt,
    Literal,
    PrintStmt,
    Variable,
    VarStmt,
)
from codefab.executor import Environment, ExecutorUnit
from codefab.resolver import OptimizedExecutorUnit, Resolver
from codefab.tokens import Token, TokenType

NESTING_DEPTH = 10  # PDF 예시(13중 중첩 블록)를 축소한 깊이


def build_deeply_nested_program(depth: int):
    """{ var a = 0; { { ... { a = a + 1; a = a + 1; a = a + 1; print a; } ... } } }

    바깥에서 선언한 변수 a 를 depth 단계 안쪽 블록에서 세 번 갱신하고 출력한다.
    최적화 전이라면 참조할 때마다 depth 번 enclosing 을 타고 올라가야(O(depth))
    하고, 최적화 후에는 미리 계산된 distance 로 한 번에 접근해야(O(1)) 한다.
    """
    var_stmt = VarStmt(make_identifier_token("a"), Literal(0.0))

    increment_refs = []
    innermost_statements = []
    for _ in range(3):
        ref = Variable(make_identifier_token("a"))
        increment_refs.append(ref)
        assign = Assign(
            make_identifier_token("a"),
            Binary(ref, Token(TokenType.PLUS, "+", literal=None, line=1), Literal(1.0)),
        )
        innermost_statements.append(ExpressionStmt(assign))

    final_ref = Variable(make_identifier_token("a"))
    innermost_statements.append(PrintStmt(final_ref))

    block = BlockStmt(innermost_statements)
    for _ in range(depth - 1):
        block = BlockStmt([block])

    program = [BlockStmt([var_stmt, block])]
    return program, increment_refs, final_ref


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


def test_깊게_중첩된_블록에서도_최적화_후에는_거리가_미리_고정되어_동적_조회를_하지_않는다(
    mocker, capsys
):
    # PDF: 최적화후: O(1), 미리 계산된 거리를 통해 즉시 접근
    program, increment_refs, final_ref = build_deeply_nested_program(NESTING_DEPTH)

    Resolver().resolve(program)

    # 선언된 스코프(가장 바깥 블록)까지의 거리는 중첩 깊이(depth)와 같아야 한다
    for ref in increment_refs:
        assert ref.distance == NESTING_DEPTH
    assert final_ref.distance == NESTING_DEPTH

    get_spy = mocker.spy(Environment, "get")
    assign_spy = mocker.spy(Environment, "assign")
    OptimizedExecutorUnit().execute(program)

    assert capsys.readouterr().out.splitlines() == ["3"]
    # distance 로 바로 접근하므로 깊이(depth)와 무관하게 동적 조회는 한 번도 없어야 한다
    get_spy.assert_not_called()
    assign_spy.assert_not_called()


def test_최적화_전에는_깊이만큼_스코프를_거슬러_올라가는_동적_조회를_한다(
    mocker, capsys
):
    # PDF: 최적화전: O(depth), depth 는 중첩된 블록 수
    # Resolver 를 거치지 않으므로 distance 가 붙지 않고, 기존 동적 조회로 동작해야 한다.
    program, increment_refs, final_ref = build_deeply_nested_program(NESTING_DEPTH)

    for ref in increment_refs:
        assert getattr(ref, "distance", None) is None
    assert getattr(final_ref, "distance", None) is None

    get_spy = mocker.spy(Environment, "get")
    assign_spy = mocker.spy(Environment, "assign")
    ExecutorUnit().execute(program)

    assert capsys.readouterr().out.splitlines() == ["3"]
    # distance 가 없으므로 참조/대입마다 enclosing 을 거슬러 올라가는 동적 조회를 탄다
    get_spy.assert_called()
    assign_spy.assert_called()


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
