"""REPL / 파일 실행 / 디버거 기능을 한 화면에서 눌러볼 수 있는 Streamlit 데모 앱.

실행: streamlit run streamlit_app.py
"""

import queue
import threading
import time
from pathlib import Path

import streamlit as st

from codefab.app.debug import DebugExecutor, DebugExitRequested, Debugger
from codefab.app.visualize import (
    build_ast_graph,
    build_token_graph,
    render_ast_dot,
    render_token_dot,
)
from codefab.assembler.function_assembler import FunctionAssembler
from codefab.assembler.function_statement_parser import FunctionStatementParser
from codefab.common.tokenizer import Tokenizer
from codefab.pipeline.optimized_interpreter import (
    OptimizingChecker,
    create_optimized_interpreter,
)

SLIDES: list[dict] = [
    {
        "kicker": "5일차 발표",
        "title": "CodeFab Interpreter\n프로젝트 발표",
        "page": "1 / 14",
        "body": """
1일차 Assembler · Checker · Executor 3단 구조 설계부터,
3~4일차 함수·클래스·배열·모듈·최적화 기능 확장까지 — **Bug Hunters**

- 조원 소개
- 구조 설계
- 기능 확장
- BP 사례
- 프로젝트 시연
- 소감
""",
    },
    {
        "kicker": "00 · 목차 (Agenda)",
        "title": "목차",
        "page": "2 / 14",
        "body": """
| 섹션 | 내용 |
| --- | --- |
| 01 · 조원 소개 및 역할 | Bug Hunters 5인, 1일차 최초 구현 → 3~4일차 확장까지 이어진 담당 영역 정리 |
| 02 · 구조 설계 | Assembler · Checker · Executor 3단 파이프라인을 처음 세운 과정 |
| 03 · 기능 구현 소개 | 완성된 파이프라인 구조 + 3~4일차 Chapter별 확장 기능 정리 |
| 04 · Best Practice 6선 | 실제 GitHub 리뷰 이력(PR #91/#65/#69/#64)과 코드 구조 패턴 기준 |
| 05 · 프로젝트 시연 | 파일 · REPL · 디버그 모드 순서로 기능이 실제로 맞물려 동작하는 모습을 시연 |
| 06 · 소감 | 조원별 한 줄 회고 |
""",
    },
    {
        "kicker": "01 · Team & Roles",
        "title": "조원 소개 및 역할",
        "page": "3 / 14",
        "body": """
팀명: **Bug Hunters**

| 이름 | 역할 |
| --- | --- |
| 김병남 | 프로젝트 초기 설정 · CI/커버리지 파이프라인 · 브랜치 컨벤션 → CLI/REPL 통합 · import(Ch.6) · 전체 통합 테스트 총괄 |
| 조승주 | Tokenizer/Token 구현 · Statement Parser 초안 → 디버그 모드(Ch.7 공장 제어 쉘) 구현 |
| 이하섭 | 테스트케이스 작성 · Executor Unit 최초 구현 → 클래스(Ch.3) 기능 전체 구현 · Executor 리팩토링 |
| 최현준 | Assembler Unit · Expression Parser 구현 → 정적 배열(Ch.4) · 실행 전 최적화(Ch.5) · 문법 리팩토링 |
| 이준원 | AST 노드 인터페이스 · Checker Unit 최초 구현 → 함수(Ch.2) 기능 초기 구현 · 에러 모듈 통합 |
""",
    },
    {
        "kicker": "02 · Day 1 · Foundation",
        "title": "구조 설계",
        "page": "4 / 14",
        "body": """
Assembler · Checker · Executor Unit 구조 설계

| Unit | 1일차 최초 구현 내용 |
| --- | --- |
| Assembler Unit | Tokenizer로 소스를 토큰화하고, Expression/Statement Parser로 AST를 구성한다. |
| Checker Unit | AST 노드 인터페이스를 정의하고, accept/visit_* 방식으로 변수 중복 선언·선언 전 사용 같은 정적 오류를 미리 잡는다. |
| Executor Unit | Checker를 통과한 AST를 순회하며 실제로 실행한다 — 이 3단 구조가 이후 함수·클래스·최적화 등 모든 확장의 토대가 됐다. |
| 팀 인프라 | 프로젝트 초기 설정 · CI/커버리지 파이프라인 · PR·브랜치 컨벤션이 이후 협업 방식의 기반을 마련했다. |
""",
    },
    {
        "kicker": "03 · Architecture",
        "title": "인터프리터 파이프라인 구조 (완성형)",
        "page": "5 / 14",
        "body": """
1일차의 3단 구조가 3~4일차를 거치며, 소스 코드 한 줄이 결과가 되기까지 이렇게 4단을 통과하게 됐습니다.

`소스(.laugh) → Tokenizer → Assembler(Parser) → Checker → Executor → 출력`

| 끼어드는 단계 | 설명 |
| --- | --- |
| Checker → Resolver/Optimizer | Ch.5 요구사항: 변수 정적 바인딩(distance 계산) + 리터럴 상수 폴딩을 Checker 통과 후 Executor 전에 수행 |
| Assembler ↔ ModuleLoader | Ch.6 import 문을 만나면 대상 파일을 재귀적으로 어셈블·검증 후 현재 스코프에 값으로 바인딩 |
""",
    },
    {
        "kicker": "03 · Feature Map",
        "title": "Chapter별 기능 구현 요약 (3~4일차 확장)",
        "page": "6 / 14",
        "body": """
| Chapter | 구현 기능 (핵심 파일) |
| --- | --- |
| Ch.1 기초 | 변수 · 조건문 · 반복문 · 연산자 (tokenizer.py, checker.py, executor_unit.py) |
| Ch.2 함수 | 함수 선언·호출·재귀·return (function_checker.py, function_executor.py, function_interpreter.py) |
| Ch.3 클래스 | 선언·인스턴스·필드·메서드·this·생성자·상속·super·instanceof (executor_unit.py의 LaughClass/LaughInstance) |
| Ch.4 배열 | 고정 크기 정적 배열, 인덱스 읽기/쓰기, 런타임 오류 검사 (array_nodes.py) |
| Ch.5 최적화 | 정적 변수 바인딩(O(1) 조회), 상수 표현식 폴딩 (resolver.py, optimizer.py) |
| Ch.6 import | 파일 import, 별칭 바인딩, 순환/중복 import 검사 (module_loader.py) |
| Ch.7 쉘 | 프롬프트(REPL) · 파일 · 디버그(step/breakpoint/watch) 3가지 실행 모드 (cli.py, app/repl.py, app/debug.py) |
""",
    },
    {
        "kicker": "BP 1/6 · TDD 전략",
        "title": '알려진 결함을 "실패하는 테스트"로 못박는다',
        "page": "7 / 14",
        "body": """
PR #91: 고치지 않은 버그를 방치하는 대신, xfail(strict=True)로 실패 자체를 스펙으로 남긴다.

PR #91 · tests/integration/test_known_gaps_integration.py

```python
@pytest.mark.xfail(strict=True, reason=
    "함수 기능이 codefab.cli가 쓰는 base Interpreter에 배선되지 않음")
def test_함수_선언과_호출_매개변수_전달(tmp_path):
    # 지금은 실패해야 정상 — 원하는 최종 동작을 그대로 assert
    result = run_cli(script, cwd=tmp_path)
    assert result.stdout == "10\\n"
```

| 효과 | 설명 |
| --- | --- |
| 실패 고정 | 지금은 실패해야 정상 — 우연한 XPASS와 진짜 회귀를 구분해준다. |
| 자동 승격 신호 | 버그가 고쳐지는 순간 XPASS로 CI가 스스로 실패 → "golden 테스트로 승격시켜라"는 신호가 사람의 기억력에 의존하지 않는다. |
| 추적성 연결 | 이후 Issue #93(print 다중값 미지원)처럼 실제 이슈로도 등록되어 별도로 추적된다. |
""",
    },
    {
        "kicker": "BP 2/6 · 리뷰 문화",
        "title": '리뷰는 "읽기"가 아니라 "실행"으로 끝낸다',
        "page": "8 / 14",
        "body": """
PR #65: 파서 결과만 보지 않고 실제로 인터프리터를 돌려봐야 파이프라인 전체가 동작하는지 알 수 있다.

PR #65 · 가져오기(import) 통합 누락(wiring gap) 발견

> **리뷰어(kimbyungnam):**
> `Interpreter().interpret('가져오기 "sum.txt" 별칭 sum;')` → Checker에 visit_import_stmt가 없어 런타임 에러
>
> **작성자:**
> 이번 PR은 파싱까지만, Checker/Executor는 다음 PR에서 순차 연결하겠습니다.

| 확인 관점 | 의미 |
| --- | --- |
| 실행 기반 검증 | 테스트가 파서 결과만 검증하면, 파이프라인 전체가 동작한다는 보장이 안 된다. |
| 스코프 명확화 | 리뷰에서 발견된 갭엔 "이번 PR 범위 아님"을 명확히 답하고 다음 PR로 넘긴다. |
| 반복되는 패턴 | CLAUDE.md의 "함수는 기본 파이프라인에 배선되지 않았다" 경고와 동일한 패턴. |
""",
    },
    {
        "kicker": "BP 3/6 · 리뷰 코멘트",
        "title": "무엇이 왜 틀렸는지, 재현 예시로 짚는다",
        "page": "9 / 14",
        "body": """
PR #69: "무엇이 왜 틀렸는지 + 재현 예시"가 있는 코멘트는 왕복 없이 한 번에 수정으로 이어진다.

PR #69 · 배열 인덱스 표현식 버그

> **리뷰어(hasuplee):**
> line_of_expr가 `arr[0] = 10;` 같은 배열 인덱스 라인에서 실패합니다. → 재현 코드 스니펫 포함
>
> **작성자:**
> 즉시 반영 → 왕복 없이 APPROVED

| 요소 | 왜 효과적인가 |
| --- | --- |
| 무엇이 틀렸는지 | 추상적 지적("버그가 있어요")이 아니라 정확한 실패 지점을 짚는다. |
| 재현 예시 포함 | 작성자가 직접 재현할 필요 없이 바로 원인을 확인할 수 있다. |
| 왕복 최소화 | 한 번의 코멘트 → 한 번의 수정 → 승인으로 리뷰 사이클이 끝난다. |
""",
    },
    {
        "kicker": "BP 4/6 · 설계 문서화",
        "title": '설계 결정에는 "왜"를 코멘트로 남긴다',
        "page": "10 / 14",
        "body": """
PR #64: 대안을 검토했지만 채택하지 않은 이유까지 남기면, 같은 질문이 반복되지 않는다.

PR #64 · CLI 진입점 통합

> **리뷰어:**
> `codefab <경로>`처럼 인자 유무로 파일 모드를 판단하면 어떨까요?
>
> **작성자:**
> 이후 `debug <경로>`가 추가되면 'debug'라는 단어가 파일 경로로 오인될 수 있어, 서브커맨드로 모드를 명시하는 구조를 유지했습니다.

| 효과 | 설명 |
| --- | --- |
| 미래 확장 근거 | 실제로 이후 PR #69에서 debug 서브커맨드가 추가되며 이 결정이 맞았음이 증명됐다. |
| 반복 질문 방지 | 왜 이렇게 설계했는지 기록해두면 같은 질문이 나중에 또 나오지 않는다. |
| 대안까지 기록 | 채택한 안뿐 아니라 검토했던 대안(인자 기반 판단)도 남아 맥락이 보존된다. |
""",
    },
    {
        "kicker": "BP 5/6 · 리팩토링",
        "title": "공통 로직은 그대로, 달라지는 지점만 훅으로 연다",
        "page": "11 / 14",
        "body": """
베이스 클래스를 고치지 않고, 딱 한 지점을 훅으로 뽑아 서브클래스가 오버라이드하게 만든다.

codefab/checker.py → codefab/function_checker.py

```python
# Checker: 메서드 순회 로직을 훅 하나로 분리
def _visit_method_body(self, method) -> None:
    for statement in method.body:
        statement.accept(self)

# FunctionChecker: 이 훅 하나만 오버라이드해서 확장
def _visit_method_body(self, method) -> None:
    self.function_depth += 1
    try:
        super()._visit_method_body(method)
    finally:
        self.function_depth -= 1
```

| 원칙 | 적용 |
| --- | --- |
| 개방-폐쇄 원칙 | Checker의 기존 코드는 한 줄도 안 건드리고 FunctionChecker만 확장했다. |
| 단일 진입점 | "메서드 본문을 어떻게 순회하는가"가 코드베이스 전체에서 딱 한 곳에만 존재한다. |
| 회귀 위험 최소화 | 기존 클래스 검사 동작은 그대로 보존된 채로 "메서드 내부 반환" 지원이 추가됐다. |
""",
    },
    {
        "kicker": "BP 6/6 · 언어 설계",
        "title": "다국어 표기는 렉서 한 층에서 끝낸다",
        "page": "12 / 14",
        "body": """
한글·영어 표기는 토크나이저에서만 구분하고, 그 아래 계층은 표기 언어를 몰라도 되게 만든다.

codefab/tokens.py

```python
KEYWORDS = {
    "var": TokenType.VAR,       "변수": TokenType.VAR,
    "class": TokenType.CLASS,   "클래스": TokenType.CLASS,
    "func": TokenType.FUN,      "함수": TokenType.FUN,
    "return": TokenType.RETURN, "반환": TokenType.RETURN,
}
# AST / Checker / Executor는 TokenType만 보고, 표기는 신경 쓰지 않는다
```

| 계층 | 언어 인식 여부 |
| --- | --- |
| Tokenizer | 한글·영어 표기를 모두 인식해 같은 TokenType으로 통일한다. |
| AST / Checker / Executor | 표기 언어와 완전히 무관 — TokenType enum 값만 보고 동작한다. |
| 확장 비용 | 새 표기를 추가할 때 KEYWORDS 테이블 한 줄만 고치면 된다. 실제로 func/return이 함수/반환과 동일하게 동작함을 테스트로 검증했다. |
""",
    },
    {
        "id": "demo_scenario",
        "kicker": "05 · Live Demo",
        "title": "프로젝트 시연 시나리오",
        "page": "13 / 14",
        "body": (
            "파일 모드 → REPL → 디버그 모드 순서로, "
            "Chapter 1~7 기능이 실제로 맞물려 동작하는 모습을 보여줍니다.\n\n"
            "왼쪽에서 순서를 고르면 오른쪽 터미널에서 바로 실행해볼 수 있습니다."
        ),
        "steps": [
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
        ],
    },
    {
        "kicker": "06 · Retrospective",
        "title": "소감",
        "page": "14 / 14",
        "body": """
| 이름 | 소감 (초안 — 발표 전 자유롭게 수정) |
| --- | --- |
| 김병남 | 1일차에 세운 CI/브랜치 컨벤션이 있어서, 여러 브랜치를 하나의 파이프라인으로 배선할 때도 안심하고 통합할 수 있었다. |
| 조승주 | 1일차에 만든 토크나이저가 끝까지 그대로 쓰였다 — 한글 키워드 하나 추가하는 것도 그 설계가 받쳐줘야 쉬워진다는 걸 알았다. |
| 이하섭 | 1일차 Executor Unit을 클래스로 확장하면서, this/super 바인딩 같은 작은 디테일이 큰 버그로 이어진다는 걸 체감했다. |
| 최현준 | 최적화는 정답을 바꾸지 않는 선에서만 해야 한다는 원칙을 지키는 게 생각보다 까다로웠다. |
| 이준원 | 1일차에 Checker를 먼저 설계해두니, 뒤에 오는 기능들이 그 위에 안전하게 쌓일 수 있었다. |

*소감은 초안입니다 — 발표 전 각자의 생각으로 자유롭게 수정하세요.*
""",
    },
]


def _render_presentation() -> None:
    st.session_state.setdefault("slide_idx", 0)
    total = len(SLIDES)

    nav_prev, nav_jump, nav_next = st.columns([1, 3, 1])
    with nav_prev:
        if st.button(
            "이전", key="slide_prev", disabled=st.session_state.slide_idx == 0
        ):
            st.session_state.slide_idx -= 1
            st.rerun()
    with nav_next:
        if st.button(
            "다음", key="slide_next", disabled=st.session_state.slide_idx == total - 1
        ):
            st.session_state.slide_idx += 1
            st.rerun()
    with nav_jump:
        st.select_slider(
            "슬라이드 이동",
            options=list(range(total)),
            value=st.session_state.slide_idx,
            format_func=lambda i: f"{i + 1}. {SLIDES[i]['title'].splitlines()[0]}",
            key="slide_idx",
        )

    slide = SLIDES[st.session_state.slide_idx]
    with st.container(border=True):
        st.caption(f"{slide['kicker']}  ·  {slide['page']}")
        st.markdown(f"## {slide['title']}")
        st.markdown(slide["body"])

        if slide.get("id") == "demo_scenario":
            _render_demo_scenario_panel(slide["steps"])


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

    slides_tab, demo_tab = st.tabs(["발표자료", "프로젝트 시연"])

    with slides_tab:
        _render_presentation()

    with demo_tab:
        repl_tab, file_tab, debug_tab, viz_tab = st.tabs(
            ["REPL", "파일 실행", "디버거", "AST/토큰 시각화"]
        )
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
