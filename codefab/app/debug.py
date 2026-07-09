from collections.abc import Callable

from codefab.array_nodes import ArrayLiteral, IndexGet, IndexSet
from codefab.assembler.function_assembler import FunctionAssembler
from codefab.ast_nodes import (
    Assign,
    Binary,
    BlockStmt,
    Call,
    ClassStmt,
    Expr,
    ExpressionStmt,
    ForStmt,
    FunctionStmt,
    Get,
    Grouping,
    IfStmt,
    ImportStmt,
    InstanceOf,
    Literal,
    Logical,
    PrintStmt,
    ReturnStmt,
    Set,
    Stmt,
    Super,
    This,
    Unary,
    Variable,
    VarStmt,
)
from codefab.executor_unit import Environment
from codefab.optimized_interpreter import (
    OptimizedFunctionExecutorUnit,
    OptimizingChecker,
)

DEFAULT_ENCODING = "utf-8"
_UNSET = object()
_EXIT_COMMANDS = {"exit", "quit"}


class DebugExitRequested(Exception):
    """디버그 세션에서 exit/quit 입력 시 실행을 즉시 중단하기 위한 내부 신호."""


def line_of_expr(expr: Expr) -> int:
    if isinstance(expr, Literal):
        return expr.line
    if isinstance(expr, Variable):
        return expr.name.line
    if isinstance(expr, Assign):
        return expr.name.line
    if isinstance(expr, (Binary, Logical, Unary)):
        return expr.operator.line
    if isinstance(expr, Grouping):
        return line_of_expr(expr.expression)
    if isinstance(expr, (ArrayLiteral, IndexGet, IndexSet)):
        return expr.line
    if isinstance(expr, Call):
        return expr.paren.line
    if isinstance(expr, (This, Super)):
        return expr.keyword.line
    if isinstance(expr, (Get, Set)):
        return expr.name.line
    if isinstance(expr, InstanceOf):
        return line_of_expr(expr.object)
    return 1


def line_of_stmt(stmt: Stmt) -> int:
    if isinstance(stmt, VarStmt):
        return stmt.name.line
    if isinstance(stmt, (PrintStmt, ExpressionStmt)):
        return line_of_expr(stmt.expression)
    if isinstance(stmt, IfStmt):
        return line_of_expr(stmt.condition)
    if isinstance(stmt, ForStmt):
        if stmt.initializer is not None:
            return line_of_stmt(stmt.initializer)
        if stmt.condition is not None:
            return line_of_expr(stmt.condition)
        return 1
    if isinstance(stmt, (ClassStmt, FunctionStmt)):
        return stmt.name.line
    if isinstance(stmt, ReturnStmt):
        return stmt.keyword.line
    if isinstance(stmt, ImportStmt):
        return stmt.path.line
    return 1


def _type_name(value: object) -> str:
    if isinstance(value, bool):
        return "Boolean"
    if isinstance(value, float):
        return "Number"
    if isinstance(value, str):
        return "String"
    return type(value).__name__


def _stringify(value: object) -> str:
    if isinstance(value, bool):
        return "참" if value else "거짓"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _lookup(environment: Environment, name: str) -> object:
    if name in environment.values:
        return environment.values[name]
    if environment.enclosing is not None:
        return _lookup(environment.enclosing, name)
    return _UNSET


class Debugger:
    def __init__(
        self,
        source_lines: list[str],
        input_source: Callable[[], str] | None = None,
        output: Callable[[str], None] | None = None,
    ):
        self._source_lines = source_lines
        self._input = input_source if input_source is not None else input
        self._output = output if output is not None else print
        self._prompt = "> "
        self._breakpoints: set[int] = set()
        self._watches: list[str] = []
        self._run_to_breakpoint = False
        self._next_until_depth: int | None = None

    def before_stmt(self, line: int, depth: int, environment: Environment) -> None:
        if self._run_to_breakpoint:
            if line not in self._breakpoints:
                return
            stopped_by_breakpoint = True
        else:
            stopped_by_breakpoint = False
            if self._next_until_depth is not None and depth > self._next_until_depth:
                return  # next로 건너뛰기로 한 블록/반복문 내부 - 멈추지 않는다

        self._run_to_breakpoint = False
        self._next_until_depth = None

        text = self._line_text(line)
        reason = " (breakpoint)" if stopped_by_breakpoint else ""
        self._output(f"[DEBUG] {line}번째 줄에서 정지{reason} -> {text}")
        self._print_watch_values(environment)
        self._read_commands(environment, depth)

    def _line_text(self, line: int) -> str:
        if 0 < line <= len(self._source_lines):
            return self._source_lines[line - 1].strip()
        return ""

    def _print_watch_values(self, environment: Environment) -> None:
        for name in self._watches:
            value = _lookup(environment, name)
            if value is not _UNSET:
                self._output(f"[WATCH] {name} = {_stringify(value)}")

    def _show_prompt(self) -> None:
        # 기본 출력(print)일 때는 줄바꿈 없이 찍어서 입력이 프롬프트와 같은 줄에 오게 한다.
        if self._output is print:
            print(self._prompt, end="", flush=True)
        else:
            self._output(self._prompt)

    def _read_commands(self, environment: Environment, depth: int) -> None:
        while True:
            self._show_prompt()
            command = self._input().strip()

            if command in _EXIT_COMMANDS:
                raise DebugExitRequested
            if command == "step":
                return
            if command == "next":
                self._next_until_depth = depth
                return
            if command == "continue":
                self._run_to_breakpoint = True
                return
            if command.startswith("break "):
                self._add_breakpoint(command)
            elif command == "breakpoints":
                self._list_breakpoints()
            elif command.startswith("remove "):
                self._remove_breakpoint(command)
            elif command.startswith("watch "):
                self._add_watch(command)
            elif command.startswith("unwatch "):
                self._remove_watch(command)
            elif command == "watches":
                self._print_watches(environment)
            elif command == "inspect":
                self._inspect(environment)

    def _add_breakpoint(self, command: str) -> None:
        line_no = int(command.split(maxsplit=1)[1])
        self._breakpoints.add(line_no)
        self._output(f"[DEBUG] {line_no}번째 줄에 breakpoint 설정")

    def _list_breakpoints(self) -> None:
        for line_no in sorted(self._breakpoints):
            self._output(f"[DEBUG] breakpoint: {line_no}번째 줄")

    def _remove_breakpoint(self, command: str) -> None:
        line_no = int(command.split(maxsplit=1)[1])
        self._breakpoints.discard(line_no)
        self._output(f"[DEBUG] {line_no}번째 줄 breakpoint 해제")

    def _add_watch(self, command: str) -> None:
        name = command.split(maxsplit=1)[1]
        if name not in self._watches:
            self._watches.append(name)
        self._output(f"[WATCH] '{name}' 감시 등록")

    def _remove_watch(self, command: str) -> None:
        name = command.split(maxsplit=1)[1]
        if name in self._watches:
            self._watches.remove(name)
        self._output(f"[WATCH] '{name}' 감시 해제")

    def _print_watches(self, environment: Environment) -> None:
        for name in self._watches:
            value = _lookup(environment, name)
            if value is not _UNSET:
                self._output(f"{name} = {_stringify(value)}")

    def _inspect(self, environment: Environment) -> None:
        self._output("--현재 스코프 변수 ----------")
        env: Environment | None = environment
        while env is not None:
            label = "전역" if env.enclosing is None else "로컬"
            for name, value in env.values.items():
                self._output(
                    f"[{label}] {name} = {_stringify(value)} ({_type_name(value)})"
                )
            env = env.enclosing


class DebugExecutor(OptimizedFunctionExecutorUnit):
    def __init__(self, debugger: Debugger):
        super().__init__()
        self._debugger = debugger

    def _before_stmt(self, statement: Stmt, depth: int) -> None:
        if isinstance(statement, BlockStmt):
            return  # 블록 여는 지점 자체는 멈춤 지점이 아니고, 안쪽 statement들만 멈춘다
        self._debugger.before_stmt(line_of_stmt(statement), depth, self.environment)


class DebugRunner:
    def __init__(
        self,
        output: Callable[[str], None] | None = None,
        input_source: Callable[[], str] | None = None,
    ):
        self._output = output if output is not None else print
        self._input = input_source

    def run_file(self, path: str) -> int:
        try:
            with open(path, encoding=DEFAULT_ENCODING) as f:
                source = f.read()
        except OSError:
            self._output(f"파일 오류: '{path}' 파일을 찾을 수 없거나 열 수 없습니다.")
            return 1

        self._output(f"[DEBUG] 소스코드 로딩 : {path}")

        try:
            statements = FunctionAssembler().assemble(source)
            OptimizingChecker().resolve(statements)
        except Exception as exc:  # noqa: BLE001 — 파이프라인 각 단계의 예외 타입이 제각각이라 광범위하게 잡음
            self._output(str(exc))
            return 1

        debugger = Debugger(
            source.splitlines(), input_source=self._input, output=self._output
        )
        try:
            DebugExecutor(debugger).execute(statements)
        except DebugExitRequested:
            return 0
        except Exception as exc:  # noqa: BLE001
            self._output(str(exc))
            return 1

        return 0
