from codefab.array_nodes import ArrayLiteral, IndexGet, IndexSet
from codefab.ast_nodes import (
    Assign,
    Binary,
    BlockStmt,
    Call,
    ClassStmt,
    Expr,
    ExpressionStmt,
    ForStmt,
    Get,
    Grouping,
    IfStmt,
    InstanceOf,
    Literal,
    Logical,
    PrintStmt,
    Set,
    Stmt,
    Super,
    This,
    Unary,
    Variable,
    VarStmt,
)
from codefab.error import (
    ArrayIndexNotNumberError,
    ArrayIndexOutOfRangeError,
    ArraySizeNotNumberError,
    DivisionByZeroError,
    InvalidOperandTypeError,
    MismatchedPlusOperandTypeError,
    NotIndexableError,
    OnlyInstancesHaveFieldsError,
    SuperclassMustBeClassError,
    UndefinedPropertyError,
    UndefinedVariableError,
    UnsupportedBinaryOperatorError,
    UnsupportedExpressionError,
    UnsupportedStatementError,
    UnsupportedUnaryOperatorError,
)
from codefab.tokens import Token, TokenType

_THIS_KEY = "this"
_SUPER_KEY = "super"
_INIT_METHOD_NAMES = ("init", "생성자")


class Environment:
    def __init__(self, enclosing: "Environment | None" = None):
        self.values: dict[str, object] = {}
        self.enclosing = enclosing

    def define(self, lexeme: str, value: object):
        self.values[lexeme] = value

    def get(self, name_token: Token) -> object:
        lexeme = name_token.lexeme

        if lexeme in self.values:
            return self.values[lexeme]

        if self.enclosing is not None:
            return self.enclosing.get(name_token)

        raise UndefinedVariableError(lexeme, line=name_token.line)

    def assign(self, name_token: Token, value: object):
        lexeme = name_token.lexeme

        if lexeme in self.values:
            self.values[lexeme] = value
            return

        if self.enclosing is not None:
            self.enclosing.assign(name_token, value)
            return

        raise UndefinedVariableError(lexeme, line=name_token.line)

    def get_by_name(self, name: str) -> object:
        """'this'/'super' 처럼 소스 문법과 무관하게 내부적으로 고정된 이름으로
        바인딩되는 값을 조회한다. Checker가 이미 유효성을 보장하므로 항상 존재한다."""
        if name in self.values:
            return self.values[name]
        if self.enclosing is not None:
            return self.enclosing.get_by_name(name)
        raise KeyError(name)


class LaughFunction:
    """클래스 메서드(생성자 포함)를 표현하는 런타임 콜러블."""

    def __init__(
        self, name: str, params: list[Token], body: list[Stmt], closure: Environment
    ):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure

    def bind(self, instance: "LaughInstance") -> "LaughFunction":
        environment = Environment(self.closure)
        environment.define(_THIS_KEY, instance)
        return LaughFunction(self.name, self.params, self.body, environment)


class LaughClass:
    def __init__(
        self,
        name: str,
        superclass: "LaughClass | None",
        methods: dict[str, LaughFunction],
    ):
        self.name = name
        self.superclass = superclass
        self.methods = methods

    def find_method(self, name: str) -> LaughFunction | None:
        if name in self.methods:
            return self.methods[name]
        if self.superclass is not None:
            return self.superclass.find_method(name)
        return None

    def find_initializer(self) -> LaughFunction | None:
        for name in _INIT_METHOD_NAMES:
            method = self.find_method(name)
            if method is not None:
                return method
        return None

    def is_same_or_subclass_of(self, other: "LaughClass") -> bool:
        current: LaughClass | None = self
        while current is not None:
            if current is other:
                return True
            current = current.superclass
        return False

    def __str__(self) -> str:
        return self.name


class LaughInstance:
    def __init__(self, klass: LaughClass):
        self.klass = klass
        self.fields: dict[str, object] = {}

    def get(self, name_token: Token) -> object:
        if name_token.lexeme in self.fields:
            return self.fields[name_token.lexeme]

        method = self.klass.find_method(name_token.lexeme)
        if method is not None:
            return method.bind(self)

        raise UndefinedPropertyError(name_token.lexeme, line=name_token.line)

    def set(self, name_token: Token, value: object):
        self.fields[name_token.lexeme] = value

    def __str__(self) -> str:
        return f"{self.klass.name} instance"


class ExecutorUnit:
    def __init__(self):
        self.environment = Environment()

    def execute(self, statements: list[Stmt]):
        for statement in statements:
            self._execute_stmt(statement)

    def _before_stmt(self, statement: Stmt) -> None:
        """서브클래스가 각 Stmt 실행 직전에 끼어들 수 있는 훅. 기본은 아무 것도 안 함."""

    def _execute_stmt(self, statement: Stmt):
        self._before_stmt(statement)

        if isinstance(statement, PrintStmt):
            value = self._evaluate_expr(statement.expression)
            print(self._stringify(value))
            return

        if isinstance(statement, ExpressionStmt):
            self._evaluate_expr(statement.expression)
            return

        if isinstance(statement, VarStmt):
            value = None
            if statement.initializer is not None:
                value = self._evaluate_expr(statement.initializer)
            self.environment.define(statement.name.lexeme, value)
            return

        if isinstance(statement, BlockStmt):
            self._execute_block(statement.statements, Environment(self.environment))
            return

        if isinstance(statement, IfStmt):
            if self._is_truthy(self._evaluate_expr(statement.condition)):
                self._execute_stmt(statement.then_branch)
            elif statement.else_branch is not None:
                self._execute_stmt(statement.else_branch)
            return

        if isinstance(statement, ForStmt):
            if statement.initializer is not None:
                self._execute_stmt(statement.initializer)

            while statement.condition is None or self._is_truthy(
                self._evaluate_expr(statement.condition)
            ):
                self._execute_stmt(statement.body)
                if statement.increment is not None:
                    self._evaluate_expr(statement.increment)
            return

        if isinstance(statement, ClassStmt):
            self._execute_class_stmt(statement)
            return

        raise UnsupportedStatementError(type(statement).__name__)

    def _execute_class_stmt(self, statement: ClassStmt):
        superclass = None
        if statement.superclass is not None:
            superclass = self._evaluate_expr(statement.superclass)
            if not isinstance(superclass, LaughClass):
                raise SuperclassMustBeClassError(line=statement.name.line)

        method_environment = self.environment
        if superclass is not None:
            method_environment = Environment(self.environment)
            method_environment.define(_SUPER_KEY, superclass)

        methods: dict[str, LaughFunction] = {
            method.name.lexeme: LaughFunction(
                method.name.lexeme, method.params, method.body, method_environment
            )
            for method in statement.methods
        }

        klass = LaughClass(statement.name.lexeme, superclass, methods)
        self.environment.define(statement.name.lexeme, klass)

    def _execute_block(self, statements: list[Stmt], environment: Environment):
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self._execute_stmt(statement)
        finally:
            self.environment = previous

    def _evaluate_expr(self, expression: Expr) -> object:
        if isinstance(expression, Literal):
            return expression.value

        if isinstance(expression, Variable):
            return self._look_up_variable(expression.name)

        if isinstance(expression, Assign):
            return self._evaluate_assign(expression)

        if isinstance(expression, Grouping):
            return self._evaluate_expr(expression.expression)

        if isinstance(expression, Unary):
            return self._evaluate_unary(expression)

        if isinstance(expression, Logical):
            return self._evaluate_logical(expression)

        if isinstance(expression, Binary):
            return self._evaluate_binary(expression)

        if isinstance(expression, This):
            return self.environment.get_by_name(_THIS_KEY)

        if isinstance(expression, Super):
            return self._evaluate_super(expression)

        if isinstance(expression, Get):
            return self._evaluate_get(expression)

        if isinstance(expression, Set):
            return self._evaluate_set(expression)

        if isinstance(expression, Call):
            return self._evaluate_call(expression)

        if isinstance(expression, InstanceOf):
            return self._evaluate_instance_of(expression)
        if isinstance(expression, ArrayLiteral):
            return self._evaluate_array_literal(expression)

        if isinstance(expression, IndexGet):
            return self._evaluate_index_get(expression)

        if isinstance(expression, IndexSet):
            return self._evaluate_index_set(expression)

        raise UnsupportedExpressionError(type(expression).__name__)

    def _evaluate_super(self, expression: Super) -> object:
        superclass: LaughClass = self.environment.get_by_name(_SUPER_KEY)
        instance = self.environment.get_by_name(_THIS_KEY)

        method = superclass.find_method(expression.method.lexeme)
        if method is None:
            raise UndefinedPropertyError(
                expression.method.lexeme, line=expression.method.line
            )
        return method.bind(instance)

    def _evaluate_get(self, expression: Get) -> object:
        obj = self._evaluate_expr(expression.object)
        if not isinstance(obj, LaughInstance):
            raise OnlyInstancesHaveFieldsError(line=expression.name.line)
        return obj.get(expression.name)

    def _evaluate_set(self, expression: Set) -> object:
        obj = self._evaluate_expr(expression.object)
        if not isinstance(obj, LaughInstance):
            raise OnlyInstancesHaveFieldsError(line=expression.name.line)
        value = self._evaluate_expr(expression.value)
        obj.set(expression.name, value)
        return value

    def _evaluate_call(self, expression: Call) -> object:
        callee = self._evaluate_expr(expression.callee)
        arguments = [self._evaluate_expr(argument) for argument in expression.arguments]
        return self._call(callee, arguments)

    def _call(self, callee: object, arguments: list[object]) -> object:
        if isinstance(callee, LaughClass):
            instance = LaughInstance(callee)
            initializer = callee.find_initializer()
            if initializer is not None:
                self._invoke_function(initializer.bind(instance), arguments)
            return instance

        if isinstance(callee, LaughFunction):
            return self._invoke_function(callee, arguments)

        return None

    def _invoke_function(
        self, function: LaughFunction, arguments: list[object]
    ) -> object:
        environment = Environment(function.closure)
        for param, argument in zip(function.params, arguments):
            environment.define(param.lexeme, argument)
        self._execute_block(function.body, environment)
        return None

    def _evaluate_instance_of(self, expression: InstanceOf) -> object:
        obj = self._evaluate_expr(expression.object)
        klass = self._evaluate_expr(expression.klass)
        if not isinstance(klass, LaughClass) or not isinstance(obj, LaughInstance):
            return False
        return obj.klass.is_same_or_subclass_of(klass)

    def _look_up_variable(self, name_token: Token) -> object:
        return self.environment.get(name_token)

    def _evaluate_assign(self, expression: Assign) -> object:
        value = self._evaluate_expr(expression.value)
        self.environment.assign(expression.name, value)
        return value

    def _is_truthy(self, value: object) -> bool:
        if value is None:
            return False

        if isinstance(value, bool):
            return value

        return True

    def _evaluate_unary(self, expression: Unary) -> object:
        right = self._evaluate_expr(expression.right)

        operator_type = expression.operator.type
        line = expression.operator.line

        if operator_type == TokenType.MINUS:
            if not isinstance(right, float):
                raise InvalidOperandTypeError(line=line)
            return -right

        if operator_type == TokenType.BANG:
            return not self._is_truthy(right)

        raise UnsupportedUnaryOperatorError(expression.operator.lexeme, line=line)

    def _evaluate_logical(self, expression: Logical) -> object:
        left = self._evaluate_expr(expression.left)

        if expression.operator.type == TokenType.OR:
            if self._is_truthy(left):
                return left
        else:
            if not self._is_truthy(left):
                return left

        return self._evaluate_expr(expression.right)

    def _evaluate_binary(self, expression: Binary) -> object:
        left = self._evaluate_expr(expression.left)
        right = self._evaluate_expr(expression.right)

        operator_type = expression.operator.type
        line = expression.operator.line

        if operator_type == TokenType.PLUS:
            if isinstance(left, str) and isinstance(right, str):
                return left + right
            if isinstance(left, float) and isinstance(right, float):
                return left + right
            raise MismatchedPlusOperandTypeError(line=line)

        if operator_type == TokenType.MINUS:
            self._check_number_operands(left, right, line)
            return left - right

        if operator_type == TokenType.STAR:
            self._check_number_operands(left, right, line)
            return left * right

        if operator_type == TokenType.SLASH:
            self._check_number_operands(left, right, line)

            if right == 0:
                raise DivisionByZeroError(line=line)

            return left / right

        if operator_type == TokenType.GREATER:
            self._check_number_operands(left, right, line)
            return left > right

        if operator_type == TokenType.GREATER_EQUAL:
            self._check_number_operands(left, right, line)
            return left >= right

        if operator_type == TokenType.LESS:
            self._check_number_operands(left, right, line)
            return left < right

        if operator_type == TokenType.LESS_EQUAL:
            self._check_number_operands(left, right, line)
            return left <= right

        if operator_type == TokenType.EQUAL_EQUAL:
            return left == right

        if operator_type == TokenType.BANG_EQUAL:
            return left != right

        raise UnsupportedBinaryOperatorError(expression.operator.lexeme, line=line)

    def _check_number_operands(self, left: object, right: object, line: int):
        if not isinstance(left, float) or not isinstance(right, float):
            raise InvalidOperandTypeError(line=line)

    def _evaluate_array_literal(self, expression: ArrayLiteral) -> object:
        size = self._evaluate_expr(expression.size)
        if not isinstance(size, float):
            raise ArraySizeNotNumberError(line=expression.line)
        return [None] * int(size)

    def _evaluate_index_get(self, expression: IndexGet) -> object:
        target = self._evaluate_expr(expression.target)
        index = self._resolve_array_index(target, expression.index, expression.line)
        return target[index]

    def _evaluate_index_set(self, expression: IndexSet) -> object:
        target = self._evaluate_expr(expression.target)
        index = self._resolve_array_index(target, expression.index, expression.line)
        value = self._evaluate_expr(expression.value)
        target[index] = value
        return value

    def _resolve_array_index(self, target: object, index_expr: Expr, line: int) -> int:
        if not isinstance(target, list):
            raise NotIndexableError(type(target).__name__, line=line)

        index_value = self._evaluate_expr(index_expr)
        if not isinstance(index_value, float):
            raise ArrayIndexNotNumberError(line=line)

        index = int(index_value)
        if index < 0 or index >= len(target):
            raise ArrayIndexOutOfRangeError(line=line)

        return index

    def _stringify(self, value: object) -> str:
        if isinstance(value, bool):
            return "참" if value else "거짓"

        if isinstance(value, float) and value.is_integer():
            return str(int(value))

        return str(value)
