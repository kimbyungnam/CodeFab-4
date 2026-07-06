"""Expr 노드 정의 (PDF p.42~43 '구현해야할 Expr 정리' 기준).

지금 1단계 TDD 루프에서는 Literal 만 사용하지만, 나머지 노드도 데이터 클래스라
미리 정의해둔다. 이후 단계(Variable/Unary/Binary/Grouping/Logical/Assign)를
TDD로 추가할 때 여기 필드를 그대로 쓰면 된다.
"""


class Expr:
    """모든 표현식(Expr) 노드의 베이스 클래스."""


class Literal(Expr):
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, Literal) and self.value == other.value

    def __repr__(self):
        return f"Literal({self.value!r})"


class Variable(Expr):
    def __init__(self, name):
        self.name = name  # Token(IDENTIFIER)

    def __repr__(self):
        return f"Variable({self.name.origin})"


class Assign(Expr):
    def __init__(self, name, value):
        self.name = name  # Token(IDENTIFIER)
        self.value = value  # Expr

    def __repr__(self):
        return f"Assign({self.name.origin}, {self.value!r})"


class Unary(Expr):
    def __init__(self, operator, right):
        self.operator = operator  # Token
        self.right = right  # Expr

    def __repr__(self):
        return f"Unary({self.operator.origin}, {self.right!r})"


class Binary(Expr):
    def __init__(self, left, operator, right):
        self.left = left  # Expr
        self.operator = operator  # Token
        self.right = right  # Expr

    def __repr__(self):
        return f"Binary({self.left!r}, {self.operator.origin}, {self.right!r})"


class Logical(Expr):
    def __init__(self, left, operator, right):
        self.left = left  # Expr
        self.operator = operator  # Token (AND / OR)
        self.right = right  # Expr

    def __repr__(self):
        return f"Logical({self.left!r}, {self.operator.origin}, {self.right!r})"


class Grouping(Expr):
    def __init__(self, expression):
        self.expression = expression  # Expr

    def __repr__(self):
        return f"Grouping({self.expression!r})"
