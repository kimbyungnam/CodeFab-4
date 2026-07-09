from codefab.assembler.expression_parser import ExpressionParser
from codefab.ast_nodes import Call, Expr
from codefab.error import MissingRightParenAfterArgumentsError
from codefab.tokens import TokenType


class CallExpressionParser(ExpressionParser):
    """ExpressionParser에 함수 호출 표현식(`add(1, 2)`) 파싱을 추가한다.

    ExpressionParser._unary()는 `self._primary()`를 호출하도록 되어 있어서,
    이 서브클래스의 인스턴스에서 실행되면 다형성에 의해 아래에서 오버라이드한
    _primary가 대신 호출된다. 그래서 기존 ExpressionParser의 문법 규칙은 한 줄도
    바꾸지 않고 postfix call 파싱만 끼워 넣을 수 있다.
    """

    def _primary(self) -> Expr:
        expression = super()._primary()
        return self._finish_calls(expression)

    def _finish_calls(self, callee: Expr) -> Expr:
        while self._match(TokenType.LEFT_PAREN):
            callee = self._finish_call(callee)
        return callee

    def _finish_call(self, callee: Expr) -> Call:
        arguments: list[Expr] = []
        if not self._check(TokenType.RIGHT_PAREN):
            arguments.append(self._assignment())
            while self._match(TokenType.COMMA):
                arguments.append(self._assignment())

        paren = self._consume(
            TokenType.RIGHT_PAREN, MissingRightParenAfterArgumentsError
        )
        return Call(callee=callee, paren=paren, arguments=arguments)
