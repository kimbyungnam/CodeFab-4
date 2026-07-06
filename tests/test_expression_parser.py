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
from codefab.tokens import Token, TokenType


def test_single_number_literal_is_parsed_as_literal_expr():
    # "3" 이라는 소스코드가 토큰화되었다고 가정한 Token List (Tokenizer 담당 결과물 대신 직접 구성)
    tokens = [
        Token(TokenType.NUMBER, "3", line=1, literal=3.0),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert expression == Literal(3.0)


def test_string_literal_is_parsed_as_literal_expr():
    tokens = [
        Token(TokenType.STRING, '"hi"', line=1, literal="hi"),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert expression == Literal("hi")


def test_true_literal_is_parsed_as_literal_expr():
    tokens = [
        Token(TokenType.TRUE, "true", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    assert ExpressionParser(tokens).parse() == Literal(True)


def test_false_literal_is_parsed_as_literal_expr():
    tokens = [
        Token(TokenType.FALSE, "false", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    assert ExpressionParser(tokens).parse() == Literal(False)


def test_identifier_is_parsed_as_variable_expr():
    tokens = [
        Token(TokenType.IDENTIFIER, "a", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Variable)
    assert expression.name.lexeme == "a"


def test_parenthesized_expression_is_parsed_as_grouping_expr():
    # "(3)"
    tokens = [
        Token(TokenType.LEFT_PAREN, "(", literal=None, line=1),
        Token(TokenType.NUMBER, "3", line=1, literal=3.0),
        Token(TokenType.RIGHT_PAREN, ")", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Grouping)
    assert expression.expression == Literal(3.0)


def test_missing_closing_paren_raises_parse_error():
    from codefab.assembler.errors import ParseError

    tokens = [
        Token(TokenType.LEFT_PAREN, "(", literal=None, line=1),
        Token(TokenType.NUMBER, "3", line=1, literal=3.0),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    with __import__("pytest").raises(ParseError):
        ExpressionParser(tokens).parse()


def test_unary_minus_is_parsed_as_unary_expr():
    # "-a"
    tokens = [
        Token(TokenType.MINUS, "-", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "a", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Unary)
    assert expression.operator.lexeme == "-"
    assert isinstance(expression.right, Variable)


def test_star_expression_is_parsed_as_binary_expr():
    # "a * b"
    tokens = [
        Token(TokenType.IDENTIFIER, "a", literal=None, line=1),
        Token(TokenType.STAR, "*", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "b", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == "*"
    assert isinstance(expression.left, Variable)
    assert isinstance(expression.right, Variable)


def test_slash_expression_is_parsed_as_binary_expr():
    # "a / b"
    tokens = [
        Token(TokenType.IDENTIFIER, "a", literal=None, line=1),
        Token(TokenType.SLASH, "/", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "b", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == "/"


def test_plus_expression_is_parsed_as_binary_expr():
    # "a + b"
    tokens = [
        Token(TokenType.IDENTIFIER, "a", literal=None, line=1),
        Token(TokenType.PLUS, "+", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "b", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == "+"


def test_minus_expression_is_parsed_as_binary_expr():
    # "a - b"
    tokens = [
        Token(TokenType.IDENTIFIER, "a", literal=None, line=1),
        Token(TokenType.MINUS, "-", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "b", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == "-"


def test_star_binds_tighter_than_plus():
    # "a + b * c"  ==>  Binary(+, a, Binary(*, b, c))
    tokens = [
        Token(TokenType.IDENTIFIER, "a", literal=None, line=1),
        Token(TokenType.PLUS, "+", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "b", literal=None, line=1),
        Token(TokenType.STAR, "*", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "c", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == "+"
    assert isinstance(expression.left, Variable)
    assert isinstance(expression.right, Binary)
    assert expression.right.operator.lexeme == "*"


def _binary_two_identifiers(op_type, op_origin):
    return [
        Token(TokenType.IDENTIFIER, "a", literal=None, line=1),
        Token(op_type, op_origin, literal=None, line=1),
        Token(TokenType.IDENTIFIER, "b", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]


def test_greater_expression_is_parsed_as_binary_expr():
    expression = ExpressionParser(
        _binary_two_identifiers(TokenType.GREATER, ">")
    ).parse()
    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == ">"


def test_greater_equal_expression_is_parsed_as_binary_expr():
    tokens = _binary_two_identifiers(TokenType.GREATER_EQUAL, ">=")
    expression = ExpressionParser(tokens).parse()
    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == ">="


def test_less_expression_is_parsed_as_binary_expr():
    expression = ExpressionParser(_binary_two_identifiers(TokenType.LESS, "<")).parse()
    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == "<"


def test_less_equal_expression_is_parsed_as_binary_expr():
    tokens = _binary_two_identifiers(TokenType.LESS_EQUAL, "<=")
    expression = ExpressionParser(tokens).parse()
    assert isinstance(expression, Binary)
    assert expression.operator.lexeme == "<="


def test_term_binds_tighter_than_comparison():
    # "a + b > c"  ==>  Binary(>, Binary(+, a, b), c)
    tokens = [
        Token(TokenType.IDENTIFIER, "a", literal=None, line=1),
        Token(TokenType.PLUS, "+", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "b", literal=None, line=1),
        Token(TokenType.GREATER, ">", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "c", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

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
    tokens = [
        Token(TokenType.IDENTIFIER, "a", literal=None, line=1),
        Token(TokenType.GREATER, ">", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "b", literal=None, line=1),
        Token(TokenType.EQUAL_EQUAL, "==", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "c", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
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
    tokens = [
        Token(TokenType.IDENTIFIER, "a", literal=None, line=1),
        Token(TokenType.AND, "and", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "b", literal=None, line=1),
        Token(TokenType.OR, "or", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "c", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Logical)
    assert expression.operator.lexeme == "or"
    assert isinstance(expression.left, Logical)
    assert expression.left.operator.lexeme == "and"
    assert isinstance(expression.right, Variable)


def test_equality_binds_tighter_than_and():
    # "a == b and c"  ==>  Logical(and, Binary(==, a, b), c)
    tokens = [
        Token(TokenType.IDENTIFIER, "a", literal=None, line=1),
        Token(TokenType.EQUAL_EQUAL, "==", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "b", literal=None, line=1),
        Token(TokenType.AND, "and", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "c", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Logical)
    assert expression.operator.lexeme == "and"
    assert isinstance(expression.left, Binary)
    assert expression.left.operator.lexeme == "=="
    assert isinstance(expression.right, Variable)


def test_assign_expression_is_parsed_as_assign_expr():
    # "a = 10"
    tokens = [
        Token(TokenType.IDENTIFIER, "a", literal=None, line=1),
        Token(TokenType.EQUAL, "=", literal=None, line=1),
        Token(TokenType.NUMBER, "10", line=1, literal=10.0),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Assign)
    assert expression.name.lexeme == "a"
    assert expression.value == Literal(10.0)


def test_assign_value_can_be_any_expression():
    # "x = a + b"
    tokens = [
        Token(TokenType.IDENTIFIER, "x", literal=None, line=1),
        Token(TokenType.EQUAL, "=", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "a", literal=None, line=1),
        Token(TokenType.PLUS, "+", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "b", literal=None, line=1),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Assign)
    assert expression.name.lexeme == "x"
    assert isinstance(expression.value, Binary)


def test_assign_is_right_associative():
    # "a = b = 3"  ==>  Assign(a, Assign(b, 3))
    tokens = [
        Token(TokenType.IDENTIFIER, "a", literal=None, line=1),
        Token(TokenType.EQUAL, "=", literal=None, line=1),
        Token(TokenType.IDENTIFIER, "b", literal=None, line=1),
        Token(TokenType.EQUAL, "=", literal=None, line=1),
        Token(TokenType.NUMBER, "3", line=1, literal=3.0),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    expression = ExpressionParser(tokens).parse()

    assert isinstance(expression, Assign)
    assert expression.name.lexeme == "a"
    assert isinstance(expression.value, Assign)
    assert expression.value.name.lexeme == "b"
    assert expression.value.value == Literal(3.0)


def test_invalid_assignment_target_raises_parse_error():
    from codefab.assembler.errors import ParseError

    # "3 = 4"
    tokens = [
        Token(TokenType.NUMBER, "3", line=1, literal=3.0),
        Token(TokenType.EQUAL, "=", literal=None, line=1),
        Token(TokenType.NUMBER, "4", line=1, literal=4.0),
        Token(TokenType.EOF, "", literal=None, line=1),
    ]

    with __import__("pytest").raises(ParseError):
        ExpressionParser(tokens).parse()
