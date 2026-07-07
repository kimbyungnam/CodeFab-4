class Assembler:
    def __init__(self, statement_parser):
        self.statement_parser = statement_parser

    def assemble(self):
        statements = []
        while not self.statement_parser.is_at_end():
            statements.append(self.statement_parser.parse_statement())
        return statements
