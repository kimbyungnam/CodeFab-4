from codefab.ast import (
    ArrayLiteral,
    Assign,
    Binary,
    Call,
    ClassStmt,
    Expr,
    ExpressionStmt,
    ForStmt,
    FunctionStmt,
    Get,
    Grouping,
    IfStmt,
    ImportStmt,
    IndexGet,
    IndexSet,
    InstanceOf,
    Literal,
    Logical,
    PrintStmt,
    ReturnStmt,
    Set,
    Stmt,
    Super,
    This,
    Unary,
    Variable,
    VarStmt,
)
from codefab.executor import Environment

UNSET = object()


def line_of_expr(expr: Expr) -> int:
    if isinstance(expr, Literal):
        return expr.line
    if isinstance(expr, Variable):
        return expr.name.line
    if isinstance(expr, Assign):
        return expr.name.line
    if isinstance(expr, (Binary, Logical, Unary)):
        return expr.operator.line
    if isinstance(expr, Grouping):
        return line_of_expr(expr.expression)
    if isinstance(expr, (ArrayLiteral, IndexGet, IndexSet)):
        return expr.line
    if isinstance(expr, Call):
        return expr.paren.line
    if isinstance(expr, (This, Super)):
        return expr.keyword.line
    if isinstance(expr, (Get, Set)):
        return expr.name.line
    if isinstance(expr, InstanceOf):
        return line_of_expr(expr.object)
    return 1


def line_of_stmt(stmt: Stmt) -> int:
    if isinstance(stmt, VarStmt):
        return stmt.name.line
    if isinstance(stmt, (PrintStmt, ExpressionStmt)):
        return line_of_expr(stmt.expression)
    if isinstance(stmt, IfStmt):
        return line_of_expr(stmt.condition)
    if isinstance(stmt, ForStmt):
        if stmt.initializer is not None:
            return line_of_stmt(stmt.initializer)
        if stmt.condition is not None:
            return line_of_expr(stmt.condition)
        return 1
    if isinstance(stmt, (ClassStmt, FunctionStmt)):
        return stmt.name.line
    if isinstance(stmt, ReturnStmt):
        return stmt.keyword.line
    if isinstance(stmt, ImportStmt):
        return stmt.path.line
    return 1


def type_name(value: object) -> str:
    if isinstance(value, bool):
        return "Boolean"
    if isinstance(value, float):
        return "Number"
    if isinstance(value, str):
        return "String"
    return type(value).__name__


def stringify(value: object) -> str:
    if isinstance(value, bool):
        return "참" if value else "거짓"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def lookup(environment: Environment, name: str) -> object:
    if name in environment.values:
        return environment.values[name]
    if environment.enclosing is not None:
        return lookup(environment.enclosing, name)
    return UNSET
