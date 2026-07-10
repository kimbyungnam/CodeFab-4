"""scripts/*.laugh 파일을 실행해 RPG 전투 로그처럼 보여주는 Streamlit 데모.

실행: streamlit run streamlit_adventure.py
"""

import html
import re
from pathlib import Path

import streamlit as st

from codefab.pipeline import create_optimized_interpreter


def _find_scripts_dir(start: Path) -> Path:
    """이 파일이 저장소 안에서 옮겨지더라도 scripts/ 폴더를 찾을 수 있도록,
    고정된 부모 깊이 대신 상위 디렉터리를 훑어 올라간다."""
    for directory in (start, *start.parents):
        candidate = directory / "scripts"
        if candidate.is_dir():
            return candidate
    return start / "scripts"


SCRIPTS_DIR = _find_scripts_dir(Path(__file__).resolve().parent)

CLASS_ICON = {"검사": "⚔️", "마법사": "🧙"}
MONSTER_ICON = {"고블린": "👺", "슬라임": "🟢"}

_INSTANTIATION_RE = re.compile(r"(검사|마법사|몬스터)\(([^)]*)\)")


def _icon_for(klass: str, name: str) -> str:
    if klass in CLASS_ICON:
        return CLASS_ICON[klass]
    return MONSTER_ICON.get(name, "👹")


def parse_sections(lines: list[str]) -> list[tuple[str, list[str]]]:
    """'==== 제목 ====' 라인을 기준으로 로그를 섹션 단위로 나눈다."""
    sections: list[tuple[str, list[str]]] = []
    title = None
    body: list[str] = []
    for line in lines:
        if line.startswith("===="):
            if title is not None:
                sections.append((title, body))
            title = line.strip("= ").strip()
            body = []
        else:
            body.append(line)
    if title is not None:
        sections.append((title, body))
    return sections


def parse_roster(body: list[str]) -> list[dict]:
    characters = []
    for line in body:
        if line.startswith("모험가팀:"):
            for member in line.removeprefix("모험가팀:").strip().split(", "):
                klass, name = member.split(" ", 1)
                characters.append({"team": "모험가팀", "klass": klass, "name": name})
        elif line.startswith("몬스터팀:"):
            for name in line.removeprefix("몬스터팀:").strip().split(", "):
                characters.append({"team": "몬스터팀", "klass": "몬스터", "name": name})
    return characters


def extract_initial_stats(source: str) -> tuple[dict[str, int], dict[str, int]]:
    """스크립트 소스의 생성자 호출(예: 마법사("멀린", 25, 20, 5))에서
    초기 체력/마나를 직접 읽어온다 — 전투 로그에는 한 번도 등장하지 않는
    캐릭터(예: 끝까지 공격받지 않은 마법사)도 최대치를 알 수 있어야 하기 때문."""
    hp_max: dict[str, int] = {}
    mana_max: dict[str, int] = {}
    for match in _INSTANTIATION_RE.finditer(source):
        klass, raw_args = match.group(1), match.group(2)
        args = [a.strip() for a in raw_args.split(",")]
        name = args[0].strip("\"'")
        numbers = [int(a) for a in args[1:]]
        if klass == "마법사":
            hp, mana, _atk = numbers
            mana_max[name] = mana
        else:
            hp, _atk = numbers
        hp_max[name] = hp
    return hp_max, mana_max


def _extract_actor(line: str) -> str:
    """'아서의 공격!' -> '아서', '고블린이 물어뜯는다!' -> '고블린'."""
    candidates = [idx for idx in (line.find("의 "), line.find("이 ")) if idx != -1]
    return line[: min(candidates)] if candidates else line


def process_round_body(
    body: list[str],
    hp: dict[str, int],
    mana: dict[str, int],
    hp_max: dict[str, int],
    mana_max: dict[str, int],
) -> list[dict]:
    """라운드 본문을 캐릭터별 턴 단위로 쪼갠다. 몬스터처럼 한 턴에 서술 줄이
    여러 개(공격+휴식) 나와도 같은 인물이면 하나의 턴으로 묶는다."""
    actions: list[dict] = []
    current_actor: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        if current_lines:
            actions.append(
                {
                    "actor": current_actor,
                    "lines": list(current_lines),
                    "hp": dict(hp),
                    "hp_max": dict(hp_max),
                    "mana": dict(mana),
                    "mana_max": dict(mana_max),
                }
            )
            current_lines.clear()

    i = 0
    while i < len(body):
        line = body[i]
        if line == "":
            i += 1
            continue

        is_hp, is_mana = line.endswith(" 체력:"), line.endswith(" 마나:")
        if (is_hp or is_mana) and i + 3 < len(body) and body[i + 2] == "->":
            name = line.rsplit(" ", 1)[0]
            try:
                after = int(body[i + 3])
            except ValueError:
                current_lines.append(line)
                i += 1
                continue
            (hp if is_hp else mana)[name] = after
            i += 4
            if i < len(body) and body[i] == "":
                i += 1
            continue

        actor = _extract_actor(line)
        if current_actor is not None and actor != current_actor:
            flush()
        current_actor = actor
        current_lines.append(line)
        i += 1

    flush()
    return actions


def build_steps(source: str, lines: list[str]) -> tuple[list[dict], list[dict]]:
    hp_max, mana_max = extract_initial_stats(source)
    hp, mana = dict(hp_max), dict(mana_max)
    steps: list[dict] = []
    characters: list[dict] = []

    for title, body in parse_sections(lines):
        if title == "참가자":
            characters = parse_roster(body)
            steps.append(
                {
                    "kind": "round0",
                    "hp": dict(hp),
                    "hp_max": dict(hp_max),
                    "mana": dict(mana),
                    "mana_max": dict(mana_max),
                }
            )
        elif title == "라운드":
            number = body[0] if body else "?"
            for action in process_round_body(body[1:], hp, mana, hp_max, mana_max):
                steps.append({"kind": "turn", "number": number, **action})
        elif title == "결과":
            narration = [ln for ln in body if ln]
            steps.append(
                {
                    "kind": "result",
                    "narration": narration,
                    "hp": dict(hp),
                    "hp_max": dict(hp_max),
                    "mana": dict(mana),
                    "mana_max": dict(mana_max),
                }
            )
    return steps, characters


ADVENTURE_THEME_KEY = "adventure_demo_theme"
_THEME_SCOPE = f".st-key-{ADVENTURE_THEME_KEY}"


def inject_css() -> None:
    """스타일을 .stApp 전체가 아니라 ADVENTURE_THEME_KEY 컨테이너 안으로 한정한다 —
    이 테마가 미니 게임 데모 탭에만 적용되고 다른 탭에는 새어나가지 않게 하기 위함."""
    st.markdown(
        """
        <style>
        __SCOPE__ {
            background: radial-gradient(circle at 20% 0%, #2b1b4d 0%, #120c24 55%, #05030d 100%);
            padding: 20px;
            border-radius: 16px;
        }
        __SCOPE__, __SCOPE__ p, __SCOPE__ li, __SCOPE__ label,
        __SCOPE__ .stMarkdown, __SCOPE__ .stMarkdown p {
            color: #eaeaea !important;
        }
        __SCOPE__ h1, __SCOPE__ h2, __SCOPE__ h3 { color: #f4c95d !important; text-shadow: 0 0 10px rgba(244,201,93,0.35); }
        .team-header {
            font-size: 1.1rem;
            font-weight: 800;
            color: #f4c95d !important;
            margin: 4px 0 10px 0;
        }
        __SCOPE__ .stExpander, __SCOPE__ .stCodeBlock, __SCOPE__ pre, __SCOPE__ code {
            background: rgba(0,0,0,0.55) !important;
            color: #eaeaea !important;
        }
        __SCOPE__ .stExpander summary { color: #f4c95d !important; font-weight: 700; }
        .char-card {
            background: linear-gradient(160deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
            border: 1px solid rgba(244,201,93,0.35);
            border-radius: 14px;
            padding: 12px 14px;
            margin-bottom: 10px;
        }
        .char-card.active { border-color: #f4c95d; box-shadow: 0 0 14px rgba(244,201,93,0.45); }
        .char-name { font-size: 1.05rem; font-weight: 700; color: #f5f5f5; }
        .stat-row { margin-top: 6px; }
        .stat-label { font-size: 0.78rem; color: #cfcfcf; margin-bottom: 2px; }
        .bar-bg {
            background: rgba(255,255,255,0.12);
            border-radius: 999px;
            height: 10px;
            overflow: hidden;
        }
        .bar-fill { height: 100%; border-radius: 999px; transition: width 0.4s ease; }
        .log-box {
            background: rgba(0,0,0,0.55);
            border: 1px solid rgba(244,201,93,0.25);
            border-radius: 12px;
            padding: 16px 18px;
            font-family: 'Consolas', 'D2Coding', monospace;
            font-size: 0.92rem;
            line-height: 1.7;
            color: #eaeaea;
            white-space: pre-wrap;
            min-height: 90px;
        }
        .result-banner {
            text-align: center;
            font-size: 1.6rem;
            font-weight: 800;
            padding: 18px;
            border-radius: 14px;
            background: linear-gradient(120deg, rgba(244,201,93,0.18), rgba(244,201,93,0.04));
            border: 1px solid rgba(244,201,93,0.5);
            color: #f4c95d;
        }
        .fx-banner {
            text-align: center;
            font-size: 3.4rem;
            line-height: 1;
            margin: 4px 0 10px 0;
        }
        .fx-caption {
            text-align: center;
            font-size: 0.9rem;
            color: #cfcfcf;
            margin-top: -6px;
            margin-bottom: 10px;
        }
        @keyframes fx-shake {
            0% { transform: translateX(0) scale(0.6); opacity: 0; }
            15% { opacity: 1; transform: scale(1.1); }
            30% { transform: translateX(-14px) rotate(-10deg); }
            50% { transform: translateX(12px) rotate(8deg); }
            70% { transform: translateX(-8px) rotate(-4deg); }
            100% { transform: translateX(0) rotate(0); opacity: 1; }
        }
        @keyframes fx-flash {
            0% { opacity: 0; transform: scale(0.3) rotate(-15deg); }
            35% { opacity: 1; transform: scale(1.5) rotate(6deg); }
            65% { transform: scale(0.95) rotate(-2deg); }
            100% { opacity: 1; transform: scale(1) rotate(0); }
        }
        @keyframes fx-spin {
            0% { opacity: 0; transform: scale(0.4) rotate(0deg); }
            60% { opacity: 1; transform: scale(1.25) rotate(200deg); }
            100% { opacity: 1; transform: scale(1) rotate(360deg); }
        }
        @keyframes fx-pulse {
            0% { opacity: 0; transform: scale(0.5); }
            50% { opacity: 1; transform: scale(1.3); }
            100% { opacity: 1; transform: scale(1); }
        }
        .fx-hit { animation: fx-shake 0.6s ease; filter: drop-shadow(0 0 10px rgba(255,95,109,0.7)); }
        .fx-crit { animation: fx-flash 0.7s ease; filter: drop-shadow(0 0 16px rgba(244,201,93,0.85)); }
        .fx-magic { animation: fx-spin 0.9s ease; filter: drop-shadow(0 0 14px rgba(95,198,255,0.75)); }
        .fx-heal { animation: fx-pulse 0.9s ease; filter: drop-shadow(0 0 14px rgba(124,252,152,0.75)); }
        </style>
        """.replace("__SCOPE__", _THEME_SCOPE),
        unsafe_allow_html=True,
    )


# 몬스터 턴은 '물어뜯기 + 휴식'처럼 한 턴에 서술이 여러 개 섞여 있을 수 있어서,
# 순서대로 검사해 가장 먼저 매치되는 것 하나만 보여준다 — 공격류를 회복류보다 먼저 둬서
# "휴식"이 있어도 실제 행동인 물어뜯기/공격 이펙트가 우선 표시되게 한다.
_EFFECTS = (
    ("크리티컬", "💥⚡", "fx-crit", "크리티컬 히트!"),
    ("마법", "🔮✨", "fx-magic", "마법 시전!"),
    ("물어뜯는다", "🦷💢", "fx-hit", "물어뜯기!"),
    ("공격", "⚔️💢", "fx-hit", "타격!"),
    ("포션", "💚✨", "fx-heal", "회복!"),
    ("휴식", "💚✨", "fx-heal", "회복!"),
)


def effect_for(lines: list[str]) -> tuple[str, str, str] | None:
    text = " ".join(lines)
    for keyword, emoji, css_class, caption in _EFFECTS:
        if keyword in text:
            return emoji, css_class, caption
    return None


def bar_html(value: int | None, max_value: int | None, gradient: str) -> str:
    if value is None or not max_value:
        pct = 0
        label = "대기 중"
    else:
        pct = max(0, min(100, round(value / max_value * 100)))
        label = f"{value} / {max_value}"
    return (
        f'<div class="stat-label">{label}</div>'
        f'<div class="bar-bg"><div class="bar-fill" '
        f'style="width:{pct}%; background:{gradient};"></div></div>'
    )


def render_character_card(name: str, klass: str, step: dict, *, active: bool) -> None:
    icon = _icon_for(klass, name)
    hp = step.get("hp", {}).get(name)
    hp_max = step.get("hp_max", {}).get(name)
    mana = step.get("mana", {}).get(name)
    mana_max = step.get("mana_max", {}).get(name)

    card_class = "char-card active" if active else "char-card"
    parts = [
        f'<div class="{card_class}">',
        f'<div class="char-name">{icon} {html.escape(name)} '
        f'<span style="font-size:0.8rem;color:#9d9d9d;">({html.escape(klass)})</span></div>',
        '<div class="stat-row">',
        bar_html(hp, hp_max, "linear-gradient(90deg,#ff5f6d,#7c1e2b)"),
        "</div>",
    ]
    if mana_max is not None:
        parts += [
            '<div class="stat-row">',
            bar_html(mana, mana_max, "linear-gradient(90deg,#5fc6ff,#1e4f7c)"),
            "</div>",
        ]
    parts.append("</div>")
    st.markdown("".join(parts), unsafe_allow_html=True)


def render_step(step: dict, characters: list[dict]) -> None:
    advs = [c for c in characters if c["team"] == "모험가팀"]
    mons = [c for c in characters if c["team"] == "몬스터팀"]
    active_actor = step.get("actor")

    if step["kind"] == "round0":
        st.subheader("🌄 라운드 0 · 전투 준비")
    elif step["kind"] == "turn":
        icon = _icon_for(
            next((c["klass"] for c in characters if c["name"] == active_actor), ""),
            active_actor or "",
        )
        st.subheader(f"⚔️ 라운드 {step['number']} · {icon} {active_actor}의 턴")
        effect = effect_for(step.get("lines", []))
        if effect is not None:
            emoji, css_class, caption = effect
            st.markdown(
                f'<div class="fx-banner {css_class}">{emoji}</div>'
                f'<div class="fx-caption">{html.escape(caption)}</div>',
                unsafe_allow_html=True,
            )
    else:
        st.subheader("🏁 결과")

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown('<div class="team-header">🛡️ 모험가팀</div>', unsafe_allow_html=True)
        for c in advs:
            render_character_card(
                c["name"], c["klass"], step, active=c["name"] == active_actor
            )
    with col_right:
        st.markdown(
            '<div class="team-header">👹 몬스터팀</div>', unsafe_allow_html=True
        )
        for c in mons:
            render_character_card(
                c["name"], c["klass"], step, active=c["name"] == active_actor
            )

    if step["kind"] == "round0":
        st.markdown(
            '<div class="log-box">모두 체력과 마나를 가득 채우고 전투를 준비했습니다. '
            "'다음 ▶'을 눌러 라운드 1을 시작하세요.</div>",
            unsafe_allow_html=True,
        )
        return

    narration = html.escape("\n".join(step.get("narration") or step.get("lines", [])))
    st.markdown(f'<div class="log-box">{narration}</div>', unsafe_allow_html=True)

    if step["kind"] == "result":
        result_line = step["narration"][-1] if step["narration"] else ""
        st.markdown(
            f'<div class="result-banner">{html.escape(result_line)}</div>',
            unsafe_allow_html=True,
        )
        # Streamlit은 다른 탭(AST/토큰 시각화 등)에서 위젯을 조작해도 이 탭의 코드를
        # 매번 다시 실행한다. 축하 애니메이션은 "이번 전투"당 한 번만 터지게, 마지막으로
        # 축하한 battle_run과 비교해서 이미 축하했으면 다시 재생하지 않는다.
        battle_run = st.session_state.get("battle_run", 0)
        if st.session_state.get("_celebrated_run") != battle_run:
            st.session_state._celebrated_run = battle_run
            if "모험가팀" in result_line:
                st.balloons()
            else:
                st.snow()


def render_adventure_panel(source: str) -> None:
    """단독 실행이든(streamlit_app.py) 다른 앱에 얹든(streamlit_app.py) 재사용 가능한
    전투 패널 본체. 페이지 설정/타이틀 같은 앱 단위 설정은 호출하는 쪽 책임으로 둔다.
    st.container(key=ADVENTURE_THEME_KEY)로 감싸서 inject_css()의 어두운 테마가
    이 컨테이너 안에서만 적용되고 다른 탭으로 새어나가지 않게 한다."""
    with st.container(key=ADVENTURE_THEME_KEY):
        inject_css()

        with st.expander("소스 코드 보기"):
            st.code(source, language="rust")

        if "steps" not in st.session_state or st.session_state.get("_source") != source:
            st.session_state.steps = None
            st.session_state.step_idx = 0
            st.session_state._source = source

        if st.button("▶ 전투 시작", type="primary"):
            result = create_optimized_interpreter().interpret(source)
            if result.error is not None:
                st.error(result.error)
                st.session_state.steps = None
            else:
                steps, characters = build_steps(source, result.output)
                st.session_state.steps = steps
                st.session_state.characters = characters
                st.session_state.step_idx = 0
                st.session_state.battle_run = st.session_state.get("battle_run", 0) + 1

        steps = st.session_state.get("steps")
        if not steps:
            st.info("위 버튼을 눌러 전투를 시작해 보세요.")
            return

        idx = st.session_state.step_idx
        nav_prev, nav_slider, nav_next = st.columns([1, 4, 1])
        with nav_prev:
            if st.button("◀ 이전", disabled=idx == 0):
                st.session_state.step_idx = max(0, idx - 1)
                st.rerun()
        with nav_next:
            if st.button("다음 ▶", disabled=idx == len(steps) - 1):
                st.session_state.step_idx = min(len(steps) - 1, idx + 1)
                st.rerun()
        with nav_slider:
            new_idx = st.slider(
                "장면 이동", 0, len(steps) - 1, idx, label_visibility="collapsed"
            )
            if new_idx != idx:
                st.session_state.step_idx = new_idx
                st.rerun()

        render_step(steps[st.session_state.step_idx], st.session_state.characters)


def main() -> None:
    st.set_page_config(
        page_title="CodeFab Laugh Language 데모", page_icon="⚔️", layout="wide"
    )
    st.title("⚔️ CodeFab — Laugh Language 모험 데모")

    script_paths = sorted(SCRIPTS_DIR.glob("*.laugh"))
    script_names = [p.name for p in script_paths]
    default_index = (
        script_names.index("adventure.laugh")
        if "adventure.laugh" in script_names
        else 0
    )
    selected_name = st.selectbox("실행할 스크립트", script_names, index=default_index)
    source = (SCRIPTS_DIR / selected_name).read_text(encoding="utf-8")

    render_adventure_panel(source)


if __name__ == "__main__":
    main()
