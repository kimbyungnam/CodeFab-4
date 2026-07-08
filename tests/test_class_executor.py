import pytest

from codefab.ast_nodes import (
    Binary,
    Call,
    ClassStmt,
    ExpressionStmt,
    Get,
    InstanceOf,
    Literal,
    MethodDecl,
    PrintStmt,
    Set,
    Super,
    This,
    Variable,
    VarStmt,
)
from codefab.error import (
    NotCallableError,
    OnlyInstancesHaveFieldsError,
    SuperclassMustBeClassError,
    UndefinedPropertyError,
)
from codefab.executor_unit import ExecutorUnit
from codefab.tokens import Token, TokenType


def make_identifier_token(lexeme: str, line: int = 1) -> Token:
    return Token(type=TokenType.IDENTIFIER, lexeme=lexeme, literal=None, line=line)


def make_variable(lexeme: str) -> Variable:
    return Variable(make_identifier_token(lexeme))


def make_var_stmt(lexeme: str, initializer) -> VarStmt:
    return VarStmt(make_identifier_token(lexeme), initializer)


def make_class_stmt(name: str, methods=None, superclass=None) -> ClassStmt:
    return ClassStmt(make_identifier_token(name), superclass, methods or [])


def make_method(name: str, params: list[str], body) -> MethodDecl:
    return MethodDecl(
        make_identifier_token(name), [make_identifier_token(p) for p in params], body
    )


def make_call(callee, arguments=None) -> Call:
    return Call(callee, make_identifier_token(")"), arguments or [])


def make_get(obj, name: str) -> Get:
    return Get(obj, make_identifier_token(name))


def make_set(obj, name: str, value) -> Set:
    return Set(obj, make_identifier_token(name), value)


def run_and_capture_prints(capsys, statements) -> list:
    ExecutorUnit().execute(statements)
    return capsys.readouterr().out.splitlines()


def test_클래스를_호출하면_인스턴스가_생성된다(capsys):
    # 클래스 Robot { } 변수 r = Robot(); 출력 r;
    statements = [
        make_class_stmt("Robot"),
        make_var_stmt("r", make_call(make_variable("Robot"))),
        PrintStmt(make_variable("r")),
    ]

    assert run_and_capture_prints(capsys, statements) == ["Robot instance"]


def test_인스턴스에_필드를_쓰고_읽을_수_있다(capsys):
    # 클래스 Robot { } 변수 r = Robot(); r.name = "SpeedRobot"; 출력 r.name;
    statements = [
        make_class_stmt("Robot"),
        make_var_stmt("r", make_call(make_variable("Robot"))),
        ExpressionStmt(make_set(make_variable("r"), "name", Literal("SpeedRobot"))),
        PrintStmt(make_get(make_variable("r"), "name")),
    ]

    assert run_and_capture_prints(capsys, statements) == ["SpeedRobot"]


def test_존재하지_않는_필드를_읽으면_에러를_발생시킨다():
    statements = [
        make_class_stmt("Robot"),
        make_var_stmt("r", make_call(make_variable("Robot"))),
        PrintStmt(make_get(make_variable("r"), "power")),
    ]

    with pytest.raises(UndefinedPropertyError):
        ExecutorUnit().execute(statements)


def test_인스턴스가_아닌_대상에_필드를_읽으면_에러를_발생시킨다():
    statements = [
        make_var_stmt("x", Literal(10.0)),
        PrintStmt(make_get(make_variable("x"), "field")),
    ]

    with pytest.raises(OnlyInstancesHaveFieldsError):
        ExecutorUnit().execute(statements)


def test_인스턴스가_아닌_대상에_필드를_쓰면_에러를_발생시킨다():
    statements = [
        make_var_stmt("x", Literal(10.0)),
        ExpressionStmt(make_set(make_variable("x"), "field", Literal(1.0))),
    ]

    with pytest.raises(OnlyInstancesHaveFieldsError):
        ExecutorUnit().execute(statements)


def test_호출할_수_없는_대상을_호출하면_에러를_발생시킨다():
    statements = [
        make_var_stmt("x", Literal("hello")),
        ExpressionStmt(make_call(make_variable("x"))),
    ]

    with pytest.raises(NotCallableError):
        ExecutorUnit().execute(statements)


def test_클래스가_아닌_대상을_상속하면_에러를_발생시킨다():
    statements = [
        make_var_stmt("x", Literal(10.0)),
        make_class_stmt("Robot", superclass=make_variable("x")),
    ]

    with pytest.raises(SuperclassMustBeClassError):
        ExecutorUnit().execute(statements)


def test_메서드_내부에서_나로_필드에_접근하고_갱신한다(capsys):
    # 클래스 Robot { move(dist) { 나.position = 나.position + dist; }
    #               report() { 출력 나.position; } }
    move_body = [
        ExpressionStmt(
            make_set(
                This(make_identifier_token("나")),
                "position",
                Binary(
                    make_get(This(make_identifier_token("나")), "position"),
                    Token(TokenType.PLUS, "+", None, 1),
                    make_variable("dist"),
                ),
            )
        )
    ]
    report_body = [PrintStmt(make_get(This(make_identifier_token("나")), "position"))]

    statements = [
        make_class_stmt(
            "Robot",
            methods=[
                make_method("move", ["dist"], move_body),
                make_method("report", [], report_body),
            ],
        ),
        make_var_stmt("r", make_call(make_variable("Robot"))),
        ExpressionStmt(make_set(make_variable("r"), "position", Literal(0.0))),
        ExpressionStmt(make_call(make_get(make_variable("r"), "move"), [Literal(5.0)])),
        ExpressionStmt(make_call(make_get(make_variable("r"), "report"))),
    ]

    assert run_and_capture_prints(capsys, statements) == ["5"]


def test_생성자는_인스턴스_생성시_자동으로_호출되고_인스턴스를_반환한다(capsys):
    # 클래스 Robot { init(name, speed) { 나.name = name; 나.speed = speed; } }
    # 변수 r = Robot("AndOr", 10); 출력 r.name;
    init_body = [
        ExpressionStmt(
            make_set(This(make_identifier_token("나")), "name", make_variable("name"))
        ),
        ExpressionStmt(
            make_set(This(make_identifier_token("나")), "speed", make_variable("speed"))
        ),
    ]

    statements = [
        make_class_stmt(
            "Robot", methods=[make_method("init", ["name", "speed"], init_body)]
        ),
        make_var_stmt(
            "r", make_call(make_variable("Robot"), [Literal("AndOr"), Literal(10.0)])
        ),
        PrintStmt(make_get(make_variable("r"), "name")),
    ]

    assert run_and_capture_prints(capsys, statements) == ["AndOr"]


def test_생성자_이름으로_한글_생성자도_지원한다(capsys):
    # 클래스 Robot { 생성자(name) { 나.name = name; } }
    init_body = [
        ExpressionStmt(
            make_set(This(make_identifier_token("나")), "name", make_variable("name"))
        )
    ]

    statements = [
        make_class_stmt("Robot", methods=[make_method("생성자", ["name"], init_body)]),
        make_var_stmt("r", make_call(make_variable("Robot"), [Literal("Sam")])),
        PrintStmt(make_get(make_variable("r"), "name")),
    ]

    assert run_and_capture_prints(capsys, statements) == ["Sam"]


def test_부모_메서드를_상속받아_호출할_수_있다(capsys):
    # 클래스 Robot { move(dist) { 출력 "move"; } }
    # 클래스 SpeedRobot : Robot { }
    # SpeedRobot().move(3);
    robot = make_class_stmt(
        "Robot", methods=[make_method("move", ["dist"], [PrintStmt(Literal("move"))])]
    )
    speed_robot = make_class_stmt("SpeedRobot", superclass=make_variable("Robot"))

    instance = make_call(make_variable("SpeedRobot"))
    statements = [
        robot,
        speed_robot,
        ExpressionStmt(make_call(make_get(instance, "move"), [Literal(3.0)])),
    ]

    assert run_and_capture_prints(capsys, statements) == ["move"]


def test_부모_메서드를_오버라이딩하고_Super로_부모_구현을_호출한다(capsys):
    # 클래스 Robot { move(dist) { 출력 "move"; } }
    # 클래스 SpeedRobot : Robot { move(dist) { 부모.move(dist); 출력 "Speeeed!"; } }
    robot = make_class_stmt(
        "Robot", methods=[make_method("move", ["dist"], [PrintStmt(Literal("move"))])]
    )
    speed_robot = make_class_stmt(
        "SpeedRobot",
        superclass=make_variable("Robot"),
        methods=[
            make_method(
                "move",
                ["dist"],
                [
                    ExpressionStmt(
                        make_call(
                            Super(
                                make_identifier_token("부모"),
                                make_identifier_token("move"),
                            ),
                            [make_variable("dist")],
                        )
                    ),
                    PrintStmt(Literal("Speeeed!")),
                ],
            )
        ],
    )

    instance = make_call(make_variable("SpeedRobot"))
    statements = [
        robot,
        speed_robot,
        ExpressionStmt(make_call(make_get(instance, "move"), [Literal(3.0)])),
    ]

    assert run_and_capture_prints(capsys, statements) == ["move", "Speeeed!"]


def test_instanceof는_자기_자신과_부모_클래스에_대해_참을_반환한다(capsys):
    # 클래스 Robot { } 클래스 SpeedRobot : Robot { }
    # 변수 w = SpeedRobot();
    # 출력 (w instanceof SpeedRobot); 출력 (w instanceof Robot);
    statements = [
        make_class_stmt("Robot"),
        make_class_stmt("SpeedRobot", superclass=make_variable("Robot")),
        make_var_stmt("w", make_call(make_variable("SpeedRobot"))),
        PrintStmt(InstanceOf(make_variable("w"), make_variable("SpeedRobot"))),
        PrintStmt(InstanceOf(make_variable("w"), make_variable("Robot"))),
    ]

    assert run_and_capture_prints(capsys, statements) == ["참", "참"]


def test_instanceof는_관련_없는_클래스에_대해_거짓을_반환한다(capsys):
    statements = [
        make_class_stmt("Robot"),
        make_class_stmt("Toaster"),
        make_var_stmt("w", make_call(make_variable("Robot"))),
        PrintStmt(InstanceOf(make_variable("w"), make_variable("Toaster"))),
    ]

    assert run_and_capture_prints(capsys, statements) == ["거짓"]
