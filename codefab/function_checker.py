from codefab.ast_nodes import Call, FunctionStmt, ReturnStmt
from codefab.checker import Checker
from codefab.errors import (
    DuplicateParameterError,
    DuplicateVariableError,
    ReturnOutsideFunctionError,
)


class FunctionChecker(Checker):
    """Checker에 함수 선언/호출/반환 관련 정적 검사를 추가한다.

    - 함수 이름 중복 선언 검사 (변수와 동일한 스코프 규칙을 재사용)
    - 파라미터 이름 중복 검사: `함수 foo(a, a) { ... }`
    - 함수 외부에서의 '반환' 사용 검사: `반환 5;` (함수 밖)

    Checker.resolve()는 `stmt.accept(self)`만 호출하므로, 여기서 새 노드에 대한
    visit_* 메서드만 추가하면 기존 checker.py는 전혀 건드리지 않아도 된다.
    """

    def __init__(self):
        super().__init__()
        self.function_depth = 0

    def visit_function_stmt(self, stmt: FunctionStmt):
        if stmt.name.lexeme in self.declared:
            raise DuplicateVariableError(stmt.name.line)
        self.declared.add(
            stmt.name.lexeme
        )  # 재귀 호출을 위해 본문 검사 전에 이름을 등록한다

        self.scopes.append(set())
        try:
            param_names: set[str] = set()
            for param in stmt.params:
                if param.lexeme in param_names:
                    raise DuplicateParameterError(param.line)
                param_names.add(param.lexeme)
                self.scopes[-1].add(param.lexeme)

            self.function_depth += 1
            try:
                for statement in stmt.body:
                    statement.accept(self)
            finally:
                self.function_depth -= 1
        finally:
            self.scopes.pop()

    def _visit_method_body(self, method) -> None:
        self.function_depth += 1
        try:
            super()._visit_method_body(method)
        finally:
            self.function_depth -= 1

    def visit_return_stmt(self, stmt: ReturnStmt):
        if self.function_depth == 0:
            raise ReturnOutsideFunctionError(stmt.keyword.line)
        super().visit_return_stmt(stmt)

    def visit_call(self, expr: Call):
        expr.callee.accept(self)
        for argument in expr.arguments:
            argument.accept(self)
