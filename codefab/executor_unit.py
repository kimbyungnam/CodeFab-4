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
    ImportStmt,
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
    ArrayIndexNotIntegerError,
    ArrayIndexNotNumberError,
    ArrayIndexOutOfRangeError,
    ArraySizeNegativeError,
    ArraySizeNotIntegerError,
    ArraySizeNotNumberError,
    DivisionByZeroError,
    InvalidOperandTypeError,
    MismatchedPlusOperandTypeError,
    NotIndexableError,
    OnlyInstancesHaveFieldsError,
    SuperclassMustBeClassError,
    UndefinedModuleMemberError,
    UndefinedPropertyError,
    UndefinedVariableError,
    UnsupportedBinaryOperatorError,
    UnsupportedStatementError,
    UnsupportedUnaryOperatorError,
)
from codefab.module_loader import ModuleLoader
from codefab.tokens import Token, TokenType
from codefab.visitor import Visitor

_INIT_METHOD_NAMES = ("init", "생성자")


class Environment:
    def __init__(self, enclosing: "Environment | None" = None):
        self.values: dict[str, object] = {}
        self.enclosing = enclosing
        self._this: "LaughInstance | None" = None
        self._super: "LaughClass | None" = None

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

    def bind_this(self, instance: "LaughInstance") -> None:
        """'나'(this) 키워드 바인딩 전용 슬롯. 사용자 변수의 `values` 딕셔너리와
        완전히 분리되어 있어 이름 충돌 자체가 불가능하다."""
        self._this = instance

    def get_this(self) -> "LaughInstance":
        if self._this is not None:
            return self._this
        if self.enclosing is not None:
            return self.enclosing.get_this()
        raise KeyError("this")

    def bind_super(self, superclass: "LaughClass") -> None:
        """'부모'(super) 키워드 바인딩 전용 슬롯. bind_this와 동일한 이유로
        `values` 딕셔너리와 분리되어 있다."""
        self._super = superclass

    def get_super(self) -> "LaughClass":
        if self._super is not None:
            return self._super
        if self.enclosing is not None:
            return self.enclosing.get_super()
        raise KeyError("super")


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
        environment.bind_this(instance)
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


class Module:
    """가져오기(import)로 만들어진 모듈 값. 점 표기(alias.member)로 멤버를 읽는다."""

    def __init__(self, environment: Environment):
        self._environment = environment

    def get_member(self, name_token: Token) -> object:
        try:
            return self._environment.get(name_token)
        except UndefinedVariableError:
            raise UndefinedModuleMemberError(
                name_token.lexeme, line=name_token.line
            ) from None


class ExecutorUnit(Visitor):
    def __init__(self, module_loader: ModuleLoader | None = None):
        self.environment = Environment()
        self._depth = 0
        self._module_loader = (
            module_loader if module_loader is not None else ModuleLoader()
        )

    def execute(self, statements: list[Stmt]):
        for statement in statements:
            self._execute_stmt(statement)

    def _before_stmt(self, statement: Stmt, depth: int) -> None:
        """서브클래스가 각 Stmt 실행 직전에 끼어들 수 있는 훅. 기본은 아무 것도 안 함.

        depth는 최상위 statement 목록 기준 0부터 시작해서, 블록/반복문 내부로
        재귀할 때마다 1씩 늘어난다 (디버그 모드의 `next`가 내부로 안 들어가고
        건너뛸 수 있게 구분하기 위함).
        """

    def _execute_stmt(self, statement: Stmt):
        self._before_stmt(statement, self._depth)

        self._depth += 1
        try:
            statement.accept(self)
        finally:
            self._depth -= 1

    def visit_print_stmt(self, stmt: PrintStmt):
        value = self._evaluate_expr(stmt.expression)
        print(self._stringify(value))

    def visit_expression_stmt(self, stmt: ExpressionStmt):
        self._evaluate_expr(stmt.expression)

    def visit_var_stmt(self, stmt: VarStmt):
        value = None
        if stmt.initializer is not None:
            value = self._evaluate_expr(stmt.initializer)
        self.environment.define(stmt.name.lexeme, value)

    def visit_block_stmt(self, stmt: BlockStmt):
        self._execute_block(stmt.statements, Environment(self.environment))

    def visit_if_stmt(self, stmt: IfStmt):
        if self._is_truthy(self._evaluate_expr(stmt.condition)):
            self._execute_stmt(stmt.then_branch)
        elif stmt.else_branch is not None:
            self._execute_stmt(stmt.else_branch)

    def visit_for_stmt(self, stmt: ForStmt):
        if stmt.initializer is not None:
            self._execute_stmt(stmt.initializer)

        while stmt.condition is None or self._is_truthy(
            self._evaluate_expr(stmt.condition)
        ):
            self._execute_stmt(stmt.body)
            if stmt.increment is not None:
                self._evaluate_expr(stmt.increment)

    def visit_class_stmt(self, stmt: ClassStmt):
        self._execute_class_stmt(stmt)

    def visit_import_stmt(self, stmt: ImportStmt):
        self._execute_import_stmt(stmt)

    def visit_function_stmt(self, stmt):
        raise UnsupportedStatementError(type(stmt).__name__)

    def visit_return_stmt(self, stmt):
        raise UnsupportedStatementError(type(stmt).__name__)

    def _execute_class_stmt(self, statement: ClassStmt):
        superclass = None
        method_environment = self.environment

        if statement.superclass is not None:
            superclass = self._evaluate_expr(statement.superclass)
            if not isinstance(superclass, LaughClass):
                raise SuperclassMustBeClassError(line=statement.name.line)
            method_environment = Environment(self.environment)
            method_environment.bind_super(superclass)

        methods: dict[str, LaughFunction] = {
            method.name.lexeme: LaughFunction(
                method.name.lexeme, method.params, method.body, method_environment
            )
            for method in statement.methods
        }

        klass = LaughClass(statement.name.lexeme, superclass, methods)
        self.environment.define(statement.name.lexeme, klass)

    def _execute_import_stmt(self, statement: ImportStmt):
        resolved_path = self._module_loader.resolve(statement.path.literal)
        module_statements = self._module_loader.load(
            resolved_path, referencing_line=statement.path.line
        )

        module_environment = Environment()  # 호출자 스코프와 격리된 새 환경
        self._execute_block(module_statements, module_environment)

        self.environment.define(statement.alias.lexeme, Module(module_environment))

    def _execute_block(self, statements: list[Stmt], environment: Environment):
        previous = self.environment
        try:
            self.environment = environment
            for statement in statements:
                self._execute_stmt(statement)
        finally:
            self.environment = previous

    def _evaluate_expr(self, expression: Expr) -> object:
        return expression.accept(self)

    def visit_literal(self, expr: Literal):
        return expr.value

    def visit_variable(self, expr: Variable):
        return self._look_up_variable(expr.name)

    def visit_assign(self, expr: Assign):
        return self._evaluate_assign(expr)

    def visit_grouping(self, expr: Grouping):
        return self._evaluate_expr(expr.expression)

    def visit_unary(self, expr: Unary):
        return self._evaluate_unary(expr)

    def visit_logical(self, expr: Logical):
        return self._evaluate_logical(expr)

    def visit_binary(self, expr: Binary):
        return self._evaluate_binary(expr)

    def visit_this(self, expr: This):
        return self.environment.get_this()

    def visit_super(self, expr: Super):
        return self._evaluate_super(expr)

    def visit_get(self, expr: Get):
        return self._evaluate_get(expr)

    def visit_set(self, expr: Set):
        return self._evaluate_set(expr)

    def visit_call(self, expr: Call):
        return self._evaluate_call(expr)

    def visit_instance_of(self, expr: InstanceOf):
        return self._evaluate_instance_of(expr)

    def visit_array_literal(self, expr: ArrayLiteral):
        return self._evaluate_array_literal(expr)

    def visit_index_get(self, expr: IndexGet):
        return self._evaluate_index_get(expr)

    def visit_index_set(self, expr: IndexSet):
        return self._evaluate_index_set(expr)

    def _evaluate_super(self, expression: Super) -> object:
        superclass: LaughClass = self.environment.get_super()
        instance = self.environment.get_this()

        method = superclass.find_method(expression.method.lexeme)
        if method is None:
            raise UndefinedPropertyError(
                expression.method.lexeme, line=expression.method.line
            )
        return method.bind(instance)

    def _evaluate_get(self, expression: Get) -> object:
        obj = self._evaluate_expr(expression.object)
        if isinstance(obj, Module):
            return obj.get_member(expression.name)
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
        if size < 0:
            raise ArraySizeNegativeError(line=expression.line)
        if not size.is_integer():
            raise ArraySizeNotIntegerError(line=expression.line)
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
        if not index_value.is_integer():
            raise ArrayIndexNotIntegerError(line=line)

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
