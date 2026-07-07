from codefab.assembler.statement_parser import StatementParser
from codefab.tokenizer import Tokenizer


class Assembler:
    def __init__(self, source: str):
        self.source = source

    def assemble(self) -> list:
        tokens = Tokenizer(self.source).scan_tokens()
        return StatementParser(tokens).parse()
