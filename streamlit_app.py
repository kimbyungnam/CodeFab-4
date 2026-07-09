"""REPL / 파일 실행 / 디버거 기능을 한 화면에서 눌러볼 수 있는 Streamlit 데모 앱.

실행: streamlit run streamlit_app.py
"""

import queue
import threading

import streamlit as st

from codefab.app.debug import DebugExecutor, DebugExitRequested, Debugger
from codefab.assembler.function_assembler import FunctionAssembler
from codefab.optimized_interpreter import (
    OptimizingChecker,
    create_optimized_interpreter,
)

PRESETS: dict[str, str] = {
    "산술 우선순위": "출력 (1 + 2) * 3;",
    "문자열 연결": '출력 "안녕, " + "말랑!";',
    "변수 선언과 사용": "변수 a = 10;\n변수 b = 20;\n출력 a + b;",
    "만약/아니면": '만약 (거짓) 출력 "no"; 아니면 출력 "kfc";',
    "반복문": "반복 (변수 j = 0; j < 3; j = j + 1) {\n  출력 j;\n}",
    "함수 선언과 호출": "함수 add(a, b) {\n  반환 a + b;\n}\n\n출력 add(3, 4);",
    "클래스 선언과 인스턴스 생성": "클래스 Robot { }\n변수 robot = Robot();\n출력 robot;",
    "배열 생성과 인덱스 읽기/쓰기": (
        "변수 arr = 배열(3);\narr[0] = 10;\narr[1] = 20;\narr[2] = 30;\n출력 arr[0];"
    ),
    "[에러] 세미콜론 누락": "출력 1 + 2",
    "[에러] 0으로 나눔": "출력 10 / 0;",
}


def _render_repl() -> None:
    st.subheader("REPL")

    if "repl_interpreter" not in st.session_state:
        st.session_state.repl_interpreter = create_optimized_interpreter()
        st.session_state.repl_history = []

    if st.button("세션 초기화", key="repl_reset"):
        st.session_state.repl_interpreter = create_optimized_interpreter()
        st.session_state.repl_history = []

    for code, output, error in st.session_state.repl_history:
        st.code(f">>> {code}", language=None)
        for line in output:
            st.text(line)
        if error is not None:
            st.error(error)

    code = st.chat_input("Laugh 코드를 입력하세요 (예: 변수 x = 1 + 2; 출력 x;)")
    if code:
        result = st.session_state.repl_interpreter.interpret(code)
        st.session_state.repl_history.append((code, result.output, result.error))
        st.rerun()


def _apply_preset(preset_key: str, source_key: str) -> None:
    preset = st.session_state[preset_key]
    st.session_state[source_key] = "" if preset == "(직접 입력)" else PRESETS[preset]


def _render_file_runner() -> None:
    st.subheader("파일 실행")

    st.session_state.setdefault("file_source", "")
    st.selectbox(
        "예제 프리셋",
        ["(직접 입력)", *PRESETS.keys()],
        key="file_preset",
        on_change=_apply_preset,
        args=("file_preset", "file_source"),
    )

    uploaded = st.file_uploader("또는 .laugh 파일 업로드", type=["laugh", "txt"])
    if uploaded is not None:
        st.session_state.file_source = uploaded.getvalue().decode("utf-8")

    source = st.text_area("소스 코드", height=200, key="file_source")

    if st.button("실행", key="file_run"):
        result = create_optimized_interpreter().interpret(source)
        st.code("\n".join(result.output) if result.output else "(출력 없음)")
        if result.error is not None:
            st.error(result.error)


def _debugger_worker(
    statements: list,
    source: str,
    cmd_q: "queue.Queue[str]",
    out_q: "queue.Queue[str | None]",
) -> None:
    debugger = Debugger(source.splitlines(), input_source=cmd_q.get, output=out_q.put)
    try:
        DebugExecutor(debugger).execute(statements)
    except DebugExitRequested:
        pass
    except Exception as exc:  # noqa: BLE001 — 파이프라인 각 단계의 예외 타입이 제각각이라 광범위하게 잡음
        out_q.put(str(exc))
    finally:
        out_q.put(None)


def _drain_until_ready() -> None:
    dbg = st.session_state.dbg
    while True:
        try:
            item = dbg["out_q"].get(timeout=5)
        except queue.Empty:
            dbg["log"].append("[디버거] 응답 없음 - 세션을 초기화해주세요.")
            dbg["done"] = True
            return
        if item is None:
            dbg["done"] = True
            return
        if item == "> ":
            return
        dbg["log"].append(item)


def _send(cmd: str) -> None:
    dbg = st.session_state.dbg
    dbg["cmd_q"].put(cmd)
    _drain_until_ready()


def _start_debug_session(source: str) -> None:
    try:
        statements = FunctionAssembler().assemble(source)
        OptimizingChecker().resolve(statements)
    except Exception as exc:  # noqa: BLE001 — 파이프라인 각 단계의 예외 타입이 제각각이라 광범위하게 잡음
        st.error(str(exc))
        return

    cmd_q: queue.Queue = queue.Queue()
    out_q: queue.Queue = queue.Queue()
    thread = threading.Thread(
        target=_debugger_worker, args=(statements, source, cmd_q, out_q), daemon=True
    )
    st.session_state.dbg = {
        "thread": thread,
        "cmd_q": cmd_q,
        "out_q": out_q,
        "log": [],
        "done": False,
    }
    thread.start()
    _drain_until_ready()


def _render_debugger() -> None:
    st.subheader("디버거")

    st.session_state.setdefault("debug_source", "")
    st.selectbox(
        "예제 프리셋",
        ["(직접 입력)", *PRESETS.keys()],
        key="debug_preset",
        on_change=_apply_preset,
        args=("debug_preset", "debug_source"),
    )
    source = st.text_area("소스 코드", height=200, key="debug_source")

    if st.button("디버그 시작", key="debug_start"):
        _start_debug_session(source)

    dbg = st.session_state.get("dbg")
    if dbg is None:
        return

    st.code("\n".join(dbg["log"]) if dbg["log"] else "(로그 없음)")

    done = dbg["done"]
    cols = st.columns(4)
    if cols[0].button("Step", key="debug_step", disabled=done):
        _send("step")
        st.rerun()
    if cols[1].button("Next", key="debug_next", disabled=done):
        _send("next")
        st.rerun()
    if cols[2].button("Continue", key="debug_continue", disabled=done):
        _send("continue")
        st.rerun()
    if cols[3].button("Inspect", key="debug_inspect", disabled=done):
        _send("inspect")
        st.rerun()

    bp_col, watch_col = st.columns(2)
    with bp_col:
        line_no = st.number_input(
            "Breakpoint 줄 번호", min_value=1, step=1, key="debug_bp_line"
        )
        if st.button("Breakpoint 설정", key="debug_bp_set", disabled=done):
            _send(f"break {int(line_no)}")
            st.rerun()
    with watch_col:
        watch_name = st.text_input("Watch 변수명", key="debug_watch_name")
        if st.button(
            "Watch 등록", key="debug_watch_set", disabled=done or not watch_name
        ):
            _send(f"watch {watch_name}")
            st.rerun()

    if st.button("중지", key="debug_stop", disabled=done):
        _send("exit")
        del st.session_state.dbg
        st.rerun()

    if done:
        st.success("디버그 세션이 종료되었습니다.")


def main() -> None:
    st.set_page_config(page_title="CodeFab-4 데모", layout="wide")
    st.title("CodeFab-4 (Laugh Language) 데모")

    repl_tab, file_tab, debug_tab = st.tabs(["REPL", "파일 실행", "디버거"])
    with repl_tab:
        _render_repl()
    with file_tab:
        _render_file_runner()
    with debug_tab:
        _render_debugger()


if __name__ == "__main__":
    main()
