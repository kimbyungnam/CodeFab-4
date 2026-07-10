from codefab.assembler.statement_parser import StatementParser
from codefab.ast import Stmt
from codefab.common.tokenizer import Tokenizer


class Assembler:
    def assemble(self, source: str) -> list[Stmt]:
        tokens = Tokenizer(source).scan_tokens()
        return StatementParser(tokens).parse()
