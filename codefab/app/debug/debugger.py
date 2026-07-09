from collections.abc import Callable

from codefab.app.debug.formatting import UNSET, lookup, stringify, type_name
from codefab.executor import Environment

_EXIT_COMMANDS = {"exit", "quit"}


class DebugExitRequested(Exception):
    """디버그 세션에서 exit/quit 입력 시 실행을 즉시 중단하기 위한 내부 신호."""


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
            value = lookup(environment, name)
            if value is not UNSET:
                self._output(f"[WATCH] {name} = {stringify(value)}")

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
            value = lookup(environment, name)
            if value is not UNSET:
                self._output(f"{name} = {stringify(value)}")

    def _inspect(self, environment: Environment) -> None:
        self._output("--현재 스코프 변수 ----------")
        env: Environment | None = environment
        while env is not None:
            label = "전역" if env.enclosing is None else "로컬"
            for name, value in env.values.items():
                self._output(
                    f"[{label}] {name} = {stringify(value)} ({type_name(value)})"
                )
            env = env.enclosing
