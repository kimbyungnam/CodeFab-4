"""REPL / 파일 실행 / 디버거 기능을 한 화면에서 눌러볼 수 있는 Streamlit 데모 앱.

실행: streamlit run streamlit_app.py
"""

import queue
import threading
import time
from pathlib import Path

import streamlit as st

from codefab.app.debug import DebugExecutor, DebugExitRequested, Debugger
from codefab.assembler.function_assembler import FunctionAssembler
from codefab.assembler.function_statement_parser import FunctionStatementParser
from codefab.common.tokenizer import Tokenizer
from codefab.pipeline.optimized_interpreter import (
    OptimizingChecker,
    create_optimized_interpreter,
)
from visualize import (
    build_ast_graph,
    build_token_graph,
    render_ast_dot,
    render_token_dot,
)

DEMO_SCENARIO_INTRO = (
    "파일 모드 → REPL → 디버그 모드 순서로, "
    "Chapter 1~7 기능이 실제로 맞물려 동작하는 모습을 보여줍니다.\n\n"
    "왼쪽에서 순서를 고르면 오른쪽 터미널에서 바로 실행해볼 수 있습니다."
)

DEMO_SCENARIO_STEPS: list[dict] = [
    {
        "key": "file",
        "label": "1. 파일 모드",
        "desc": "클래스+함수+상속이 함께 있는 예제 실행 → 정상 출력 확인",
    },
    {
        "key": "repl",
        "label": "2. REPL 모드",
        "desc": "변수 선언·조건문을 한 줄씩 입력해 대화형으로 실행",
    },
    {
        "key": "debug",
        "label": "3. 디버그 모드",
        "desc": "step/breakpoint/watch로 함수 호출과 변수 변화를 실시간 관찰",
    },
    {
        "key": "import",
        "label": "4. import",
        "desc": "분리된 모듈(.laugh) 파일을 불러와 변수를 재사용하는 예제 실행",
    },
    {
        "key": "error",
        "label": "5. 에러 케이스",
        "desc": "의도적으로 잘못된 스크립트 실행 → 정확한 한글 에러 메시지 확인",
    },
]

ADVENTURE_DEMO_INTRO = (
    "Chapter 3(클래스·상속)과 Chapter 5(최적화)가 실제로 맞물려 동작하는 모습을, "
    "간단한 텍스트 RPG 전투로 보여줍니다.\n\n"
    "`scripts/adventure.laugh` — 검사·마법사 파티 vs 고블린·슬라임. "
    "'다음 ▶'을 누르면 캐릭터 한 명의 턴씩 진행됩니다."
)


def _render_demo_scenario_tab() -> None:
    st.markdown("## 프로젝트 시연 시나리오")
    st.markdown(DEMO_SCENARIO_INTRO)
    _render_demo_scenario_panel(DEMO_SCENARIO_STEPS)


def _render_adventure_demo_tab() -> None:
    st.markdown("## 미니 게임 데모 — 모험가 vs 몬스터")
    st.markdown(ADVENTURE_DEMO_INTRO)
    _render_adventure_demo_panel()


def _render_adventure_demo_panel() -> None:
    """streamlit_adventure.py를 그대로 재사용한다 — 이 슬라이드 전용 로직/스타일은
    전부 그 파일에 있고, 여기서는 소스를 읽어 넘겨주기만 한다."""
    from streamlit_adventure import render_adventure_panel

    script_path = Path(__file__).resolve().parent / "scripts" / "adventure.laugh"
    render_adventure_panel(script_path.read_text(encoding="utf-8"))


_DEMO_SCENARIO_RENDERERS = {
    "file": lambda: _render_file_runner(
        key_prefix="scn_file", default_preset="클래스+함수+상속 통합 예제"
    ),
    "repl": lambda: _render_repl(key_prefix="scn_repl"),
    "debug": lambda: _render_debugger(key_prefix="scn_debug"),
    "import": lambda: _render_import_demo(),
    "error": lambda: _render_file_runner(
        key_prefix="scn_error", default_preset="[에러] 세미콜론 누락"
    ),
}


def _render_demo_scenario_panel(steps: list[dict]) -> None:
    st.session_state.setdefault("scn_active_step", steps[0]["key"])

    step_col, terminal_col = st.columns([2, 3])
    with step_col:
        for step in steps:
            active = st.session_state.scn_active_step == step["key"]
            if st.button(
                step["label"],
                key=f"scn_step_btn_{step['key']}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                st.session_state.scn_active_step = step["key"]
                st.rerun()
            st.caption(step["desc"])

    with terminal_col:
        with st.container(border=True):
            renderer = _DEMO_SCENARIO_RENDERERS[st.session_state.scn_active_step]
            renderer()


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
    "클래스+함수+상속 통합 예제": (
        "클래스 Robot {\n"
        "    생성자(name) {\n"
        "        나.name = name;\n"
        "    }\n"
        "    move(dist) {\n"
        "        출력 나.name;\n"
        "        출력 dist;\n"
        "    }\n"
        "}\n\n"
        "클래스 SpeedRobot : Robot {\n"
        "    move(dist) {\n"
        "        부모.move(dist);\n"
        '        출력 "부스터 가동!";\n'
        "    }\n"
        "}\n\n"
        "함수 greet(name) {\n"
        '    반환 "안녕, " + name;\n'
        "}\n\n"
        '변수 r = SpeedRobot("Sam");\n'
        "출력 greet(r.name);\n"
        "r.move(3);"
    ),
}


def _render_repl(key_prefix: str = "repl") -> None:
    st.subheader("REPL")

    interp_key = f"{key_prefix}_interpreter"
    hist_key = f"{key_prefix}_history"

    if interp_key not in st.session_state:
        st.session_state[interp_key] = create_optimized_interpreter()
        st.session_state[hist_key] = []

    if st.button("세션 초기화", key=f"{key_prefix}_reset"):
        st.session_state[interp_key] = create_optimized_interpreter()
        st.session_state[hist_key] = []

    for code, output, error in st.session_state[hist_key]:
        st.code(f">>> {code}", language=None)
        for line in output:
            st.text(line)
        if error is not None:
            st.error(error)

    code = st.chat_input(
        "Laugh 코드를 입력하세요 (예: 변수 x = 1 + 2; 출력 x;)",
        key=f"{key_prefix}_input",
    )
    if code:
        result = st.session_state[interp_key].interpret(code)
        st.session_state[hist_key].append((code, result.output, result.error))
        st.rerun()


def _apply_preset(preset_key: str, source_key: str) -> None:
    preset = st.session_state[preset_key]
    st.session_state[source_key] = "" if preset == "(직접 입력)" else PRESETS[preset]


def _render_file_runner(
    key_prefix: str = "file", default_preset: str | None = None
) -> None:
    st.subheader("파일 실행")

    source_key = f"{key_prefix}_source"
    preset_key = f"{key_prefix}_preset"
    st.session_state.setdefault(
        source_key, PRESETS.get(default_preset, "") if default_preset else ""
    )
    st.selectbox(
        "예제 프리셋",
        ["(직접 입력)", *PRESETS.keys()],
        index=([*PRESETS.keys()].index(default_preset) + 1 if default_preset else 0),
        key=preset_key,
        on_change=_apply_preset,
        args=(preset_key, source_key),
    )

    uploaded = st.file_uploader(
        "또는 .laugh 파일 업로드", type=["laugh", "txt"], key=f"{key_prefix}_upload"
    )
    if uploaded is not None:
        st.session_state[source_key] = uploaded.getvalue().decode("utf-8")

    source = st.text_area("소스 코드", height=200, key=source_key)

    if st.button("실행", key=f"{key_prefix}_run"):
        started = time.perf_counter()
        result = create_optimized_interpreter().interpret(source)
        elapsed_ms = (time.perf_counter() - started) * 1000

        status_col, time_col, lines_col = st.columns(3)
        status_col.metric("상태", "에러" if result.error is not None else "성공")
        time_col.metric("실행 시간", f"{elapsed_ms:.1f} ms")
        lines_col.metric("출력 줄 수", len(result.output))

        st.code("\n".join(result.output) if result.output else "(출력 없음)")
        if result.error is not None:
            st.error(result.error)


def _render_import_demo(key_prefix: str = "scn_import") -> None:
    st.subheader("import (가져오기)")
    st.caption("모듈 파일을 저장한 뒤, 메인 코드에서 가져오기(import)로 재사용합니다.")

    module_key = f"{key_prefix}_module"
    main_key = f"{key_prefix}_main"
    module_filename = f"{key_prefix}_module.laugh"

    st.session_state.setdefault(module_key, '변수 pi = 3.14;\n변수 이름 = "CodeFab";')
    st.session_state.setdefault(
        main_key,
        f'가져오기 "{module_filename}" 별칭 lib;\n출력 lib.pi;\n출력 lib.이름;',
    )

    st.text_area(f"모듈 파일 ({module_filename})", height=100, key=module_key)
    st.text_area("메인 코드", height=100, key=main_key)

    if st.button("실행", key=f"{key_prefix}_run"):
        module_path = Path.cwd() / module_filename
        try:
            module_path.write_text(st.session_state[module_key], encoding="utf-8")
            result = create_optimized_interpreter().interpret(
                st.session_state[main_key]
            )
            st.code("\n".join(result.output) if result.output else "(출력 없음)")
            if result.error is not None:
                st.error(result.error)
        finally:
            module_path.unlink(missing_ok=True)


def _render_visualizer(key_prefix: str = "viz") -> None:
    st.subheader("AST / 토큰 시각화")

    source_key = f"{key_prefix}_source"
    preset_key = f"{key_prefix}_preset"
    st.session_state.setdefault(source_key, "")
    st.selectbox(
        "예제 프리셋",
        ["(직접 입력)", *PRESETS.keys()],
        key=preset_key,
        on_change=_apply_preset,
        args=(preset_key, source_key),
    )
    source = st.text_area("소스 코드", height=150, key=source_key)

    if not source.strip():
        st.info("소스 코드를 입력하거나 프리셋을 선택하세요.")
        return

    try:
        started = time.perf_counter()
        tokens = Tokenizer(source).scan_tokens()
        statements = FunctionStatementParser(tokens).parse()
        elapsed_ms = (time.perf_counter() - started) * 1000
    except Exception as exc:  # noqa: BLE001 — 토크나이저/파서 예외 타입이 제각각이라 광범위하게 잡음
        st.error(str(exc))
        return

    token_nodes, token_edges = build_token_graph(tokens)
    ast_nodes, ast_edges = build_ast_graph(statements)

    stat_cols = st.columns(4)
    stat_cols[0].metric("토큰 수", len(tokens))
    stat_cols[1].metric("최상위 문장 수", len(statements))
    stat_cols[2].metric("AST 노드 수", len(ast_nodes))
    stat_cols[3].metric("파싱 시간", f"{elapsed_ms:.2f} ms")

    st.markdown("#### 토큰 스트림")
    st.graphviz_chart(render_token_dot(token_nodes, token_edges))

    st.markdown("#### AST (구문 트리)")
    st.graphviz_chart(render_ast_dot(ast_nodes, ast_edges))


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


def _drain_until_ready(dbg_key: str) -> None:
    dbg = st.session_state[dbg_key]
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


def _send(dbg_key: str, cmd: str) -> None:
    dbg = st.session_state[dbg_key]
    dbg["cmd_q"].put(cmd)
    _drain_until_ready(dbg_key)


def _start_debug_session(dbg_key: str, source: str) -> None:
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
    st.session_state[dbg_key] = {
        "thread": thread,
        "cmd_q": cmd_q,
        "out_q": out_q,
        "log": [],
        "done": False,
    }
    thread.start()
    _drain_until_ready(dbg_key)


def _render_debugger(key_prefix: str = "debug") -> None:
    st.subheader("디버거")

    source_key = f"{key_prefix}_source"
    preset_key = f"{key_prefix}_preset"
    dbg_key = f"{key_prefix}_dbg"

    st.session_state.setdefault(source_key, "")
    st.selectbox(
        "예제 프리셋",
        ["(직접 입력)", *PRESETS.keys()],
        key=preset_key,
        on_change=_apply_preset,
        args=(preset_key, source_key),
    )
    source = st.text_area("소스 코드", height=200, key=source_key)

    if st.button("디버그 시작", key=f"{key_prefix}_start"):
        _start_debug_session(dbg_key, source)

    dbg = st.session_state.get(dbg_key)
    if dbg is None:
        return

    st.code("\n".join(dbg["log"]) if dbg["log"] else "(로그 없음)")

    done = dbg["done"]
    cols = st.columns(4)
    if cols[0].button("Step", key=f"{key_prefix}_step", disabled=done):
        _send(dbg_key, "step")
        st.rerun()
    if cols[1].button("Next", key=f"{key_prefix}_next", disabled=done):
        _send(dbg_key, "next")
        st.rerun()
    if cols[2].button("Continue", key=f"{key_prefix}_continue", disabled=done):
        _send(dbg_key, "continue")
        st.rerun()
    if cols[3].button("Inspect", key=f"{key_prefix}_inspect", disabled=done):
        _send(dbg_key, "inspect")
        st.rerun()

    bp_col, watch_col = st.columns(2)
    with bp_col:
        line_no = st.number_input(
            "Breakpoint 줄 번호", min_value=1, step=1, key=f"{key_prefix}_bp_line"
        )
        if st.button("Breakpoint 설정", key=f"{key_prefix}_bp_set", disabled=done):
            _send(dbg_key, f"break {int(line_no)}")
            st.rerun()
    with watch_col:
        watch_name = st.text_input("Watch 변수명", key=f"{key_prefix}_watch_name")
        if st.button(
            "Watch 등록",
            key=f"{key_prefix}_watch_set",
            disabled=done or not watch_name,
        ):
            _send(dbg_key, f"watch {watch_name}")
            st.rerun()

    if st.button("중지", key=f"{key_prefix}_stop", disabled=done):
        _send(dbg_key, "exit")
        del st.session_state[dbg_key]
        st.rerun()

    if done:
        st.success("디버그 세션이 종료되었습니다.")


def main() -> None:
    st.set_page_config(page_title="CodeFab-4 데모", layout="wide")
    st.title("CodeFab-4 (Laugh Language) 데모")

    scenario_tab, adventure_tab, repl_tab, file_tab, debug_tab, viz_tab = st.tabs(
        ["시연 시나리오", "미니 게임", "REPL", "파일 실행", "디버거", "AST/토큰 시각화"]
    )
    with scenario_tab:
        _render_demo_scenario_tab()
    with adventure_tab:
        _render_adventure_demo_tab()
    with repl_tab:
        _render_repl()
    with file_tab:
        _render_file_runner()
    with debug_tab:
        _render_debugger()
    with viz_tab:
        _render_visualizer()


if __name__ == "__main__":
    main()
