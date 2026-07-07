from codefab.assembler.assembler import Assembler


class _FakeStatementParser:
    """StatementParser 완성 전까지 Assembler 를 검증하기 위한 테스트 더블.

    실제 StatementParser 는 is_at_end() / parse_statement() 인터페이스를
    구현할 예정이다.
    """

    def __init__(self, statements):
        self._statements = list(statements)

    def is_at_end(self):
        return len(self._statements) == 0

    def parse_statement(self):
        return self._statements.pop(0)


def test_assemble_returns_empty_list_when_already_at_end():
    statement_parser = _FakeStatementParser([])

    program = Assembler(statement_parser).assemble()

    assert program == []


def test_assemble_returns_single_statement():
    statement_parser = _FakeStatementParser(["stmt-1"])

    program = Assembler(statement_parser).assemble()

    assert program == ["stmt-1"]


def test_assemble_returns_statements_in_order_until_end():
    statement_parser = _FakeStatementParser(["stmt-1", "stmt-2", "stmt-3"])

    program = Assembler(statement_parser).assemble()

    assert program == ["stmt-1", "stmt-2", "stmt-3"]
