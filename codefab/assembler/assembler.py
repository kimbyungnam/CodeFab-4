from typing import Protocol


class StatementParser(Protocol):
    """Assembler 가 의존하는 Statement 파서의 계약."""

    def is_at_end(self) -> bool: ...

    def parse_statement(self): ...


class Assembler:
    def __init__(self, statement_parser: StatementParser):
        self.statement_parser = statement_parser

    def assemble(self) -> list:
        statements = []
        while not self.statement_parser.is_at_end():
            statements.append(self.statement_parser.parse_statement())
        return statements
