import pytest

from codefab.assembler.errors import ParseError
from codefab.assembler.expr import (
    Assign,
    Binary,
    Grouping,
    Literal,
    Logical,
    Unary,
    Variable,
)
from codefab.assembler.expression_parser import ExpressionParser
from codefab.tokenizer import Tokenizer
from codefab.tokens import Token, TokenType


def test_single_number_literal_is_parsed_as_literal_expr():
    tokens = Tokenizer("3").scan_tokens()

    expression = ExpressionParser(tokens).parse()

    assert expression == Literal(3.0)


def test_string_literal_is_parsed_as_literal_expr():
    # Tokenizer 가 아직 STRING 리터럴을 지원하지 않아 직접 구성한다.
    tokens = [
        Token(type=TokenType.STRING, lexeme='"hi"', literal="hi", line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert expression == Literal("hi")


def test_true_literal_is_parsed_as_literal_expr():
    # Tokenizer 가 아직 true/false 키워드를 지원하지 않아 직접 구성한다.
    tokens = [
        Token(type=TokenType.TRUE, lexeme="true", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]

    assert ExpressionParser(tokens).parse() == Literal(True)


def test_false_literal_is_parsed_as_literal_expr():
    tokens = [
        Token(type=TokenType.FALSE, lexeme="false", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]

    assert ExpressionParser(tokens).parse() == Literal(False)


def test_identifier_is_parsed_as_variable_expr():
    tokens = Tokenizer("a").scan_tokens()

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Variable)
    assert expression.name.lexeme == "a"


def test_parenthesized_expression_is_parsed_as_grouping_expr():
    tokens = Tokenizer("(3)").scan_tokens()

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Grouping)
    assert expression.expression == Literal(3.0)


def test_missing_closing_paren_raises_parse_error():
    tokens = Tokenizer("(3").scan_tokens()

    with pytest.raises(ParseError):
        ExpressionParser(tokens).parse()


def test_unary_minus_is_parsed_as_unary_expr():
    tokens = Tokenizer("-a").scan_tokens()

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Unary)
    assert expression.operator.lexeme == "-"
    assert isinstance(expression.right, Variable)


def test_star_expression_is_parsed_as_binary_expr():
    tokens = Tokenizer("a * b").scan_tokens()

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == "*"
    assert isinstance(expression.left, Variable)
    assert isinstance(expression.right, Variable)


def test_slash_expression_is_parsed_as_binary_expr():
    tokens = Tokenizer("a / b").scan_tokens()

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == "/"


def test_plus_expression_is_parsed_as_binary_expr():
    tokens = Tokenizer("a + b").scan_tokens()

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == "+"


def test_minus_expression_is_parsed_as_binary_expr():
    tokens = Tokenizer("a - b").scan_tokens()

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == "-"


def test_star_binds_tighter_than_plus():
    # "a + b * c"  ==>  Binary(+, a, Binary(*, b, c))
    tokens = Tokenizer("a + b * c").scan_tokens()

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == "+"
    assert isinstance(expression.left, Variable)
    assert isinstance(expression.right, Binary)
    assert expression.right.operator.lexeme == "*"


def _binary_two_identifiers(op_type, op_origin):
    # Tokenizer 가 아직 지원하지 않는 연산자(>=, <=, ==, and, or)용 직접 구성 헬퍼.
    return [
        Token(type=TokenType.IDENTIFIER, lexeme="a", literal=None, line=1),
        Token(type=op_type, lexeme=op_origin, literal=None, line=1),
        Token(type=TokenType.IDENTIFIER, lexeme="b", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]


def test_greater_expression_is_parsed_as_binary_expr():
    tokens = Tokenizer("a > b").scan_tokens()

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == ">"


def test_greater_equal_expression_is_parsed_as_binary_expr():
    tokens = _binary_two_identifiers(TokenType.GREATER_EQUAL, ">=")
    expression = ExpressionParser(tokens).parse()
    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == ">="


def test_less_expression_is_parsed_as_binary_expr():
    tokens = Tokenizer("a < b").scan_tokens()

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == "<"


def test_less_equal_expression_is_parsed_as_binary_expr():
    tokens = _binary_two_identifiers(TokenType.LESS_EQUAL, "<=")
    expression = ExpressionParser(tokens).parse()
    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == "<="


def test_term_binds_tighter_than_comparison():
    # "a + b > c"  ==>  Binary(>, Binary(+, a, b), c)
    tokens = Tokenizer("a + b > c").scan_tokens()

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == ">"
    assert isinstance(expression.left, Binary)
    assert expression.left.operator.lexeme == "+"
    assert isinstance(expression.right, Variable)


def test_equal_equal_expression_is_parsed_as_binary_expr():
    tokens = _binary_two_identifiers(TokenType.EQUAL_EQUAL, "==")
    expression = ExpressionParser(tokens).parse()
    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == "=="


def test_comparison_binds_tighter_than_equality():
    # "a > b == c"  ==>  Binary(==, Binary(>, a, b), c)
    # EQUAL_EQUAL 은 Tokenizer 가 아직 지원하지 않아 직접 구성한다.
    tokens = [
        Token(type=TokenType.IDENTIFIER, lexeme="a", literal=None, line=1),
        Token(type=TokenType.GREATER, lexeme=">", literal=None, line=1),
        Token(type=TokenType.IDENTIFIER, lexeme="b", literal=None, line=1),
        Token(type=TokenType.EQUAL_EQUAL, lexeme="==", literal=None, line=1),
        Token(type=TokenType.IDENTIFIER, lexeme="c", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == "=="
    assert isinstance(expression.left, Binary)
    assert expression.left.operator.lexeme == ">"
    assert isinstance(expression.right, Variable)


def test_and_expression_is_parsed_as_logical_expr():
    tokens = _binary_two_identifiers(TokenType.AND, "and")
    expression = ExpressionParser(tokens).parse()
    assert isinstance(expression, Logical)
    assert expression.operator.lexeme == "and"


def test_or_expression_is_parsed_as_logical_expr():
    tokens = _binary_two_identifiers(TokenType.OR, "or")
    expression = ExpressionParser(tokens).parse()
    assert isinstance(expression, Logical)
    assert expression.operator.lexeme == "or"


def test_and_binds_tighter_than_or():
    # "a and b or c"  ==>  Logical(or, Logical(and, a, b), c)
    # and/or 는 Tokenizer 가 아직 지원하지 않아 직접 구성한다.
    tokens = [
        Token(type=TokenType.IDENTIFIER, lexeme="a", literal=None, line=1),
        Token(type=TokenType.AND, lexeme="and", literal=None, line=1),
        Token(type=TokenType.IDENTIFIER, lexeme="b", literal=None, line=1),
        Token(type=TokenType.OR, lexeme="or", literal=None, line=1),
        Token(type=TokenType.IDENTIFIER, lexeme="c", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Logical)
    assert expression.operator.lexeme == "or"
    assert isinstance(expression.left, Logical)
    assert expression.left.operator.lexeme == "and"
    assert isinstance(expression.right, Variable)


def test_equality_binds_tighter_than_and():
    # "a == b and c"  ==>  Logical(and, Binary(==, a, b), c)
    # ==, and 는 Tokenizer 가 아직 지원하지 않아 직접 구성한다.
    tokens = [
        Token(type=TokenType.IDENTIFIER, lexeme="a", literal=None, line=1),
        Token(type=TokenType.EQUAL_EQUAL, lexeme="==", literal=None, line=1),
        Token(type=TokenType.IDENTIFIER, lexeme="b", literal=None, line=1),
        Token(type=TokenType.AND, lexeme="and", literal=None, line=1),
        Token(type=TokenType.IDENTIFIER, lexeme="c", literal=None, line=1),
        Token(type=TokenType.EOF, lexeme="", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Logical)
    assert expression.operator.lexeme == "and"
    assert isinstance(expression.left, Binary)
    assert expression.left.operator.lexeme == "=="
    assert isinstance(expression.right, Variable)


def test_assign_expression_is_parsed_as_assign_expr():
    tokens = Tokenizer("a = 10").scan_tokens()

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Assign)
    assert expression.name.lexeme == "a"
    assert expression.value == Literal(10.0)


def test_assign_value_can_be_any_expression():
    tokens = Tokenizer("x = a + b").scan_tokens()

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Assign)
    assert expression.name.lexeme == "x"
    assert isinstance(expression.value, Binary)


def test_assign_is_right_associative():
    # "a = b = 3"  ==>  Assign(a, Assign(b, 3))
    tokens = Tokenizer("a = b = 3").scan_tokens()

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Assign)
    assert expression.name.lexeme == "a"
    assert isinstance(expression.value, Assign)
    assert expression.value.name.lexeme == "b"
    assert expression.value.value == Literal(3.0)


def test_invalid_assignment_target_raises_parse_error():
    tokens = Tokenizer("3 = 4").scan_tokens()

    with pytest.raises(ParseError):
        ExpressionParser(tokens).parse()
