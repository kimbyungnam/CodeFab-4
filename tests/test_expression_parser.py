"""Expression 파싱 TDD 루프.

[1단계] 가장 단순한 표현식부터: 숫자 리터럴 하나.
다음 단계(문자열/불리언 리터럴 -> 변수 -> 단항 -> 이항/우선순위 -> 괄호 -> 논리 -> 대입)는
같은 패턴(먼저 실패하는 테스트를 추가하고, 통과할 최소 코드를 ExpressionParser에 붙이는 것)
으로 이어서 작성하면 된다.
"""

from assembler.expr import Literal
from assembler.expression_parser import ExpressionParser
from assembler.tokens import Token, TokenType


def test_single_number_literal_is_parsed_as_literal_expr():
    # "3" 이라는 소스코드가 토큰화되었다고 가정한 Token List (Tokenizer 담당 결과물 대신 직접 구성)
    tokens = [
        Token(TokenType.NUMBER, "3", line=1, literal=3.0),
        Token(TokenType.EOF, "", line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert expression == Literal(3.0)
