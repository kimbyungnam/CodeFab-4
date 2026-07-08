from codefab.assembler.function_assembler import FunctionAssembler
from codefab.ast_nodes import Call, ExpressionStmt, FunctionStmt


def test_함수_선언과_호출을_함께_조립한다():
    source = """
    함수 add(a, b) {
        반환 a + b;
    }
    add(1, 2);
    """

    statements = FunctionAssembler().assemble(source)

    assert isinstance(statements[0], FunctionStmt)
    assert isinstance(statements[1], ExpressionStmt)
    assert isinstance(statements[1].expression, Call)
