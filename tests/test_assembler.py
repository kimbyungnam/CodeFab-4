import pytest

from codefab.assembler.assembler import Assembler


class _FakeStatementParser:
    """StatementParser 완성 전까지 Assembler 를 검증하기 위한 테스트 더블."""

    def __init__(self, statements):
        self._statements = list(statements)

    def is_at_end(self):
        return len(self._statements) == 0

    def parse_statement(self):
        return self._statements.pop(0)


@pytest.mark.parametrize(
    "statements",
    [
        [],
        ["stmt-1"],
        ["stmt-1", "stmt-2", "stmt-3"],
    ],
)
def test_assemble_returns_statements_in_order(statements):
    statement_parser = _FakeStatementParser(statements)

    program = Assembler(statement_parser).assemble()

    assert program == statements
