from codefab.assembler.statement_parser import StatementParser
from codefab.tokenizer import Tokenizer


class Assembler:
    def assemble(self, source: str) -> list:
        tokens = Tokenizer(source).scan_tokens()
        return StatementParser(tokens).parse()
