from codefab.assembler.assembler import Assembler
from codefab.assembler.function_statement_parser import FunctionStatementParser
from codefab.ast import Stmt
from codefab.tokenizer import Tokenizer


class FunctionAssembler(Assembler):
    """함수 선언/호출을 인식하는 FunctionStatementParser로 조립하는 Assembler."""

    def assemble(self, source: str) -> list[Stmt]:
        tokens = Tokenizer(source).scan_tokens()
        return FunctionStatementParser(tokens).parse()
