from codefab.assembler.expression_parser import ExpressionParser
from codefab.assembler.statement_parser import StatementParser
from codefab.ast import (
    Call,
    ClassStmt,
    Get,
    InstanceOf,
    Literal,
    PrintStmt,
    ReturnStmt,
    Set,
    Super,
    This,
    Variable,
)
from codefab.tokenizer import Tokenizer
from codefab.tokens import Token, TokenType


def tokenize(source: str) -> list[Token]:
    return Tokenizer(source).scan_tokens()


def parse_expression(source: str):
    return ExpressionParser(tokenize(source)).parse()


def parse_statements(source: str):
    return StatementParser(tokenize(source)).parse()


def test_빈_클래스_선언을_파싱한다():
    # 클래스 Robot { }
    stmt = parse_statements("클래스 Robot { }")[0]

    assert isinstance(stmt, ClassStmt)
    assert stmt.name.lexeme == "Robot"
    assert stmt.superclass is None
    assert stmt.methods == []


def test_상속_구문이_있는_클래스_선언을_파싱한다():
    # 클래스 SpeedRobot : Robot { }
    stmt = parse_statements("클래스 SpeedRobot : Robot { }")[0]

    assert isinstance(stmt, ClassStmt)
    assert stmt.name.lexeme == "SpeedRobot"
    assert isinstance(stmt.superclass, Variable)
    assert stmt.superclass.name.lexeme == "Robot"


def test_매개변수가_있는_메서드_선언을_파싱한다():
    # 클래스 Robot { 생성자(name, speed) { 나.name = name; } }
    stmt = parse_statements("클래스 Robot { 생성자(name, speed) { 나.name = name; } }")[
        0
    ]

    assert len(stmt.methods) == 1
    method = stmt.methods[0]
    assert method.name.lexeme == "생성자"
    assert [p.lexeme for p in method.params] == ["name", "speed"]
    assert len(method.body) == 1

    assign = method.body[0].expression
    assert isinstance(assign, Set)
    assert isinstance(assign.object, This)
    assert assign.name.lexeme == "name"
    assert isinstance(assign.value, Variable)


def test_여러_메서드를_가진_클래스_선언을_파싱한다():
    source = "클래스 Robot { move(dist) { } report() { } }"
    stmt = parse_statements(source)[0]

    assert [m.name.lexeme for m in stmt.methods] == ["move", "report"]
    assert [p.lexeme for p in stmt.methods[0].params] == ["dist"]
    assert stmt.methods[1].params == []


def test_필드_읽기는_Get_표현식으로_파싱된다():
    # r.name
    expression = parse_expression("r.name")

    assert isinstance(expression, Get)
    assert isinstance(expression.object, Variable)
    assert expression.object.name.lexeme == "r"
    assert expression.name.lexeme == "name"


def test_필드_쓰기는_Set_표현식으로_파싱된다():
    # r.speed = 10
    expression = parse_expression("r.speed = 10")

    assert isinstance(expression, Set)
    assert expression.name.lexeme == "speed"
    assert expression.value == Literal(10.0)


def test_클래스_호출은_Call_표현식으로_파싱된다():
    # Robot()
    expression = parse_expression("Robot()")

    assert isinstance(expression, Call)
    assert isinstance(expression.callee, Variable)
    assert expression.arguments == []


def test_인자가_있는_호출을_파싱한다():
    # Robot("AndOr", 10)
    expression = parse_expression('Robot("AndOr", 10)')

    assert isinstance(expression, Call)
    assert expression.arguments == [Literal("AndOr"), Literal(10.0)]


def test_메서드_호출_체이닝을_파싱한다():
    # SpeedRobot().move(3)
    expression = parse_expression("SpeedRobot().move(3)")

    assert isinstance(expression, Call)
    assert isinstance(expression.callee, Get)
    assert expression.callee.name.lexeme == "move"
    assert isinstance(expression.callee.object, Call)
    assert expression.arguments == [Literal(3.0)]


def test_나_표현식을_파싱한다():
    expression = parse_expression("나")

    assert isinstance(expression, This)


def test_부모_메서드_호출을_파싱한다():
    # 부모.move(dist)
    expression = parse_expression("부모.move(dist)")

    assert isinstance(expression, Call)
    assert isinstance(expression.callee, Super)
    assert expression.callee.method.lexeme == "move"
    expected_arg = Variable(Token(TokenType.IDENTIFIER, "dist", None, 1))
    assert expression.arguments == [expected_arg]


def test_instanceof_표현식을_파싱한다():
    # w instanceof SpeedRobot
    expression = parse_expression("w instanceof SpeedRobot")

    assert isinstance(expression, InstanceOf)
    assert isinstance(expression.object, Variable)
    assert expression.object.name.lexeme == "w"
    assert isinstance(expression.klass, Variable)
    assert expression.klass.name.lexeme == "SpeedRobot"


def test_출력문에서_instanceof_표현식을_사용할_수_있다():
    # 출력 (w instanceof Robot);
    stmt = parse_statements("출력 (w instanceof Robot);")[0]

    assert isinstance(stmt, PrintStmt)
    grouped = stmt.expression
    assert isinstance(grouped.expression, InstanceOf)


def test_생성자_본문의_반환문은_ReturnStmt로_파싱된다():
    # 클래스 Robot { 생성자() { 반환 5; } }
    stmt = parse_statements("클래스 Robot { 생성자() { 반환 5; } }")[0]

    assert isinstance(stmt, ClassStmt)
    method = stmt.methods[0]
    assert len(method.body) == 1
    assert isinstance(method.body[0], ReturnStmt)
    assert method.body[0].value == Literal(5.0)


def test_값이_없는_반환문도_파싱된다():
    # 생성자() { 반환; }
    stmt = parse_statements("클래스 Robot { 생성자() { 반환; } }")[0]

    return_stmt = stmt.methods[0].body[0]
    assert isinstance(return_stmt, ReturnStmt)
    assert return_stmt.value is None
