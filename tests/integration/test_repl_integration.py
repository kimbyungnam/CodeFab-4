"""codefab-repl 프로세스 통합 테스트.

`tests/integration/fixtures/laugh/{normal,error}/`의 공유 `.laugh`/`.out` 쌍 중
`NORMAL_REPL_CASES`/`ERROR_REPL_CASES`에 이름이 있는 케이스만 골라, 실제
`python -m codefab.app.repl` 프로세스에 stdin으로 넣어 Assembler -> Checker -> Executor
전체 파이프라인이 올바른 출력/에러 메시지를 내는지 검증한다.

REPL(`codefab.app.repl.main`)은 멀티라인 입력을 지원한다(`Repl.run`이 괄호/블록이 안 닫혔으면
다음 줄까지 버퍼링했다가 실행) — 그래서 `.laugh` 원본을 한 줄로 합치지 않고 파일 그대로
stdin에 흘려보낸다. 또한 `main()`은 파이프라인 에러가 나도 항상 종료 코드 0을 반환하므로
exit code는 검증하지 않는다.

REPL은 CLI와 달리 실행 단위(버퍼)마다 줄 번호를 1부터 다시 센다 — 여러 줄이 괄호/블록으로
묶여 한 번에 실행되면 그 안에서의 상대 줄 번호가 CLI(`<이름>.out`)와 우연히 같아지지만,
블록 없이 문장이 한 줄씩 독립 실행되면 파일상 실제 위치와 무관하게 그 문장 하나 기준
"1번째 줄"이 된다. 이 차이를 `<이름>.out`의 절대 줄 번호로부터 계산해 보정하기 위해,
`_chunk_ranges`가 `Repl`이 실제로 사용하는 청크 판단 로직(`_is_incomplete`/`_starts_with_else`/
`_is_bare_if_without_else`)을 그대로 재사용해 REPL이 소스를 어떻게 실행 단위로 나눌지 재현하고,
`_repl_expected_error`가 그 청크 경계를 이용해 CLI의 절대 줄 번호를 REPL의 상대 줄 번호로
바꿔준다. 마지막으로, 세미콜론 누락처럼 파일 끝 개행에 의존하는 에러는 CLI가 "실제로 없는
가상의 다음 줄"까지 세지만 REPL은 stdin 줄의 개행을 rstrip하기 때문에 그 가상의 줄을 볼 수
없다 — 그래서 계산된 상대 줄 번호를 마지막 청크의 실제 줄 수로 clamp한다.

일부 케이스는 Checker에 `visit_print_stmt`/`visit_if_stmt`/`visit_for_stmt`/`visit_literal`이
아직 구현되어 있지 않아 현재 실패(red)한다 — 이는 알려진 미구현 상태이며, 해당 기능이 구현되면
이 테스트들이 통과해야 한다.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

from codefab.app.repl import Repl

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "laugh"
PROMPT_LINE = "> "
CONTINUATION_PROMPT_LINE = "... "
_LINE_PREFIX_RE = re.compile(r"^\[(\d+)번째 줄\]")

NORMAL_REPL_CASES = [
    "산술_우선순위_곱셈",
    "산술_우선순위_괄호",
    "산술_좌결합_뺄셈",
    "산술_좌결합_나눗셈",
    "단항_마이너스",
    "비교_미만",
    "비교_초과",
    "동등성_참",
    "동등성_다름",
    "문자열_연결",
    "정수_출력",
    "정수형_실수_출력",
    "소수_출력",
    "참_리터럴",
    "거짓_리터럴",
    "변수_선언과_사용",
    "변수_재할당",
    "블록_스코프와_shadowing",
    "안쪽_블록에서_바깥_변수_수정",
    "중첩_스코프_해석",
    "만약_참",
    "만약_아니면",
    "아니면은_가장_가까운_만약에_결합",
    "반복문",
    "함수_선언과_호출",
]

ERROR_REPL_CASES = [
    "세미콜론_누락",
    "닫는_괄호_누락",
    "잘못된_할당_대상",
    "표현식_자리에_잘못된_토큰",
    "지역_변수_자기_초기화식에서_읽기",
    "같은_스코프_중복_선언",
    "정의되지_않은_변수_참조",
    "덧셈에_숫자와_문자열_혼용",
    "숫자가_아닌_값에_단항_마이너스",
]


def run_repl(source: str) -> list[str]:
    result = subprocess.run(
        [sys.executable, "-m", "codefab.app.repl"],
        input=source if source.endswith("\n") else source + "\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
        timeout=10,
    )
    # 프롬프트는 줄바꿈 없이 다음 출력과 같은 줄에 이어붙어 나오므로(REPL 모드 스펙),
    # 프롬프트 문자열을 전부 제거한 뒤 실제 출력 줄만 남긴다.
    output = result.stdout.replace(PROMPT_LINE, "").replace(
        CONTINUATION_PROMPT_LINE, ""
    )
    return [line for line in output.splitlines() if line]


def _chunk_ranges(source: str) -> list[tuple[int, int]]:
    """`Repl.run`과 같은 규칙으로 소스를 실행 단위(청크)로 나눠 절대 줄 번호
    (시작, 끝) 쌍의 목록을 반환한다. 실제 실행은 하지 않고 청크 판단 메서드만
    재사용해서 `Repl.run`의 버퍼링 결과와 어긋나지 않게 한다."""
    repl = Repl(interpreter=None)
    lines = source.splitlines()
    ranges: list[tuple[int, int]] = []
    buffer: list[str] = []
    buffer_start = 1
    awaiting_else = False

    for line_no, line in enumerate(lines, start=1):
        if awaiting_else:
            awaiting_else = False
            if repl._starts_with_else(line):
                buffer.append(line)
                if repl._is_incomplete("\n".join(buffer)):
                    continue
                ranges.append((buffer_start, line_no))
                buffer = []
                continue
            ranges.append((buffer_start, line_no - 1))
            buffer = []

        if not buffer:
            buffer_start = line_no
        buffer.append(line)
        chunk_source = "\n".join(buffer)
        if repl._is_incomplete(chunk_source):
            continue
        if repl._is_bare_if_without_else(chunk_source):
            awaiting_else = True
            continue
        ranges.append((buffer_start, line_no))
        buffer = []

    if buffer:
        ranges.append((buffer_start, len(lines)))

    return ranges


def _repl_expected_error(source: str, cli_error: str) -> str:
    match = _LINE_PREFIX_RE.match(cli_error)
    if not match:
        return cli_error

    absolute_line = int(match.group(1))
    for start, end in _chunk_ranges(source):
        if absolute_line <= end:
            relative_line = min(absolute_line, end) - start + 1
            break
    else:
        # 파일 끝 개행에 의존하는 에러(예: 세미콜론 누락)는 CLI가 실제로 없는
        # 가상의 다음 줄까지 세지만, REPL은 stdin 줄의 개행을 rstrip하므로 그
        # 가상의 줄을 볼 수 없다 — 마지막 청크의 실제 줄 수로 clamp한다.
        start, end = _chunk_ranges(source)[-1]
        relative_line = end - start + 1

    return _LINE_PREFIX_RE.sub(f"[{relative_line}번째 줄]", cli_error, count=1)


def _case_params(kind: str, names: list[str]) -> list[pytest.param]:
    return [
        pytest.param(
            FIXTURES_DIR / kind / f"{name}.laugh",
            FIXTURES_DIR / kind / f"{name}.out",
            id=name,
        )
        for name in names
    ]


@pytest.mark.parametrize(
    "script, expected_file", _case_params("normal", NORMAL_REPL_CASES)
)
def test_정상동작_예제가_기대한_출력을_낸다(script, expected_file):
    expected_output = [
        line for line in expected_file.read_text(encoding="utf-8").splitlines() if line
    ]

    assert run_repl(script.read_text(encoding="utf-8")) == expected_output


@pytest.mark.parametrize(
    "script, expected_file", _case_params("error", ERROR_REPL_CASES)
)
def test_에러_예제가_기대한_에러_메시지를_낸다(script, expected_file):
    source = script.read_text(encoding="utf-8")
    cli_error = expected_file.read_text(encoding="utf-8").strip()
    expected_error = _repl_expected_error(source, cli_error)

    assert expected_error in run_repl(source)
