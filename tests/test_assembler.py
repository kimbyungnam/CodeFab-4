import pytest

from codefab.assembler.assembler import Assembler
from codefab.assembler.errors import ParseError


class _FakeStatementParser:
    """StatementParser 완성 전까지 Assembler 를 검증하기 위한 테스트 더블."""

    def __init__(self, statements):
        self._statements = list(statements)

    def is_at_end(self):
        return len(self._statements) == 0

    def parse_statement(self):
        return self._statements.pop(0)


class _FailingStatementParser:
    """일부 statement 성공 후 ParseError 를 던지는 테스트 더블."""

    def __init__(self, statements_then_error):
        self._statements = list(statements_then_error)

    def is_at_end(self):
        return False

    def parse_statement(self):
        if not self._statements:
            raise ParseError("의도적으로 발생시킨 오류", line=1)
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


def test_assemble_propagates_parse_error_without_swallowing():
    statement_parser = _FailingStatementParser(["stmt-1"])

    with pytest.raises(ParseError):
        Assembler(statement_parser).assemble()
