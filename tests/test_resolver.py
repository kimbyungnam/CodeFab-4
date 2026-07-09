import pytest

from codefab.ast import (
    Assign,
    Binary,
    BlockStmt,
    ExpressionStmt,
    ForStmt,
    Literal,
    PrintStmt,
    Variable,
    VarStmt,
)
from codefab.errors import DuplicateVariableError, SelfReferenceInInitializerError
from codefab.resolver import Resolver
from codefab.tokens import Token, TokenType


def make_identifier_token(lexeme: str, line: int = 1) -> Token:
    return Token(type=TokenType.IDENTIFIER, lexeme=lexeme, literal=None, line=line)


def test_전역_변수_참조에는_distance가_붙지_않는다():
    # var a = 1; print a;
    var_stmt = VarStmt(make_identifier_token("a"), Literal(1.0))
    variable_a = Variable(make_identifier_token("a"))
    print_stmt = PrintStmt(variable_a)

    Resolver().resolve([var_stmt, print_stmt])

    assert getattr(variable_a, "distance", None) is None


def test_바로_감싼_블록에서의_참조는_distance_0이다():
    # var a = 1; { print a; }
    var_stmt = VarStmt(make_identifier_token("a"), Literal(1.0))
    variable_a = Variable(make_identifier_token("a"))
    block = BlockStmt([ExpressionStmt(variable_a)])

    # a 는 전역이라 여전히 distance 가 없어야 한다 (전역은 정적 바인딩 대상 아님)
    Resolver().resolve([var_stmt, block])
    assert getattr(variable_a, "distance", None) is None

    # 지역 변수는 자신이 선언된 블록(distance 0)에서 참조하면 0이 붙는다
    inner_var = VarStmt(make_identifier_token("b"), Literal(2.0))
    inner_ref = Variable(make_identifier_token("b"))
    block2 = BlockStmt([inner_var, ExpressionStmt(inner_ref)])

    Resolver().resolve([block2])
    assert inner_ref.distance == 0


def test_중첩_블록에서_바깥쪽_지역변수_참조는_distance가_한단계씩_늘어난다():
    # { var b = 1; { var c = 2; { print b; } } }
    outer_var = VarStmt(make_identifier_token("b"), Literal(1.0))
    outer_ref = Variable(make_identifier_token("b"))
    inner_var = VarStmt(make_identifier_token("c"), Literal(2.0))
    innermost_block = BlockStmt([ExpressionStmt(outer_ref)])
    middle_block = BlockStmt([inner_var, innermost_block])
    outer_block = BlockStmt([outer_var, middle_block])

    Resolver().resolve([outer_block])

    # outer_ref 는 innermost_block(0) -> middle_block(1) 을 지나 outer_var 의
    # 스코프(2)에서 찾아야 하므로 distance == 2
    assert outer_ref.distance == 2


def test_for문의_초기화_변수는_조건_증감식과_같은_스코프_body에서는_한단계_위():
    # { for (var i = 0; i < 3; i = i + 1) { print i; } }
    #
    # ForStmt 는 자기 자신을 위한 스코프를 따로 만들지 않고(Executor 도 동일하게
    # initializer/condition/increment 를 감싸는 블록의 Environment 를 그대로
    # 씀), body 는 별도 BlockStmt 라 자기 스코프를 하나 더 판다. 그래서
    # condition/increment 는 distance 0, body 안에서의 참조는 distance 1 이
    # 나와야 실제 런타임 스코프 구조와 맞다. (전역에 바로 놓인 for 문이면 i 는
    # 전역 변수가 되어버려 distance 가 안 붙으므로, 이 구조를 검증하려면 바깥을
    # 블록으로 한 번 감싸야 한다.)
    i_token = make_identifier_token("i")
    initializer = VarStmt(i_token, Literal(0.0))
    condition = Binary(
        Variable(i_token), Token(TokenType.LESS, "<", None, 1), Literal(3.0)
    )
    increment = Assign(
        i_token,
        Binary(Variable(i_token), Token(TokenType.PLUS, "+", None, 1), Literal(1.0)),
    )
    body_ref = Variable(i_token)
    body = BlockStmt([ExpressionStmt(body_ref)])
    for_stmt = ForStmt(initializer, condition, increment, body)
    outer_block = BlockStmt([for_stmt])

    Resolver().resolve([outer_block])

    assert condition.left.distance == 0
    assert increment.distance == 0
    assert body_ref.distance == 1


def test_자기참조_검증은_그대로_동작한다():
    self_ref = Variable(make_identifier_token("a"))
    var_stmt = VarStmt(make_identifier_token("a"), self_ref)

    with pytest.raises(SelfReferenceInInitializerError):
        Resolver().resolve([var_stmt])


def test_중복선언_검증은_그대로_동작한다():
    block = BlockStmt(
        [
            VarStmt(make_identifier_token("a"), Literal(1.0)),
            VarStmt(make_identifier_token("a"), Literal(2.0)),
        ]
    )

    with pytest.raises(DuplicateVariableError):
        Resolver().resolve([block])
