"""codefab debug(`python -m codefab.common.cli debug <file>`) golden 테스트.

`tests/integration/fixtures/laugh/{normal,error}/`의 공유 `.laugh` 소스 중
`<이름>.debug.cmds`가 있는 케이스만 골라, 그 안의 명령을 한 줄씩 `DebugRunner`에 입력하며
캡처한 출력(stdout, [DEBUG] 로그·프롬프트·실제 print 출력 모두 포함)을 `<이름>.debug.out`과
비교한다.

`[DEBUG] 소스코드 로딩 : <path>` 줄은 실행 환경마다 절대 경로가 달라지므로, golden 파일에는
`<path>` 자리표시자를 쓰고 비교 전에 실제 경로를 그 자리표시자로 치환한다.

이 통합 테스트는 실제 파일 로딩·전체 파이프라인 실행을 거치므로 tests/integration/ 밑에
둔다 — 평소에는 pytest tests --ignore=tests/integration로 건너뛸 수 있다.

이 fixture들은 file-runner/repl 통합 테스트와 같은 `.laugh` 소스를 공유한다 — 자세한 내용은
`tests/integration/fixtures/laugh/README.md` 참고. 모든 케이스에 debug golden이 있는 것은
아니고, 대표적인 일부 케이스에만 `.debug.cmds`/`.debug.out`을 추가했다.
"""

import re
from pathlib import Path

import pytest

from codefab.app.debug import DebugRunner

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "laugh"
LOADING_LINE_RE = re.compile(r"^\[DEBUG\] 소스코드 로딩 : .*$", re.MULTILINE)


def _fake_input(commands):
    return iter(commands).__next__


def run_debug(script: Path, commands: list[str], capsys) -> str:
    runner = DebugRunner(input_source=_fake_input(commands))
    runner.run_file(str(script))
    out = capsys.readouterr().out
    return LOADING_LINE_RE.sub("[DEBUG] 소스코드 로딩 : <path>", out, count=1)


def _golden_debug_cases(kind: str) -> list[pytest.param]:
    cases = []
    for cmds_file in sorted((FIXTURES_DIR / kind).glob("*.debug.cmds")):
        stem = cmds_file.name.removesuffix(".debug.cmds")
        script = cmds_file.with_name(f"{stem}.laugh")
        expected = cmds_file.with_name(f"{stem}.debug.out")
        commands = [
            line for line in cmds_file.read_text(encoding="utf-8").splitlines() if line
        ]
        cases.append(pytest.param(script, commands, expected, id=stem))
    return cases


@pytest.mark.parametrize(
    "script, commands, expected_file", _golden_debug_cases("normal")
)
def test_공유_fixture_정상동작_예제의_debug_세션_출력이_기대와_같다(
    script, commands, expected_file, capsys
):
    expected = expected_file.read_text(encoding="utf-8")

    assert run_debug(script, commands, capsys) == expected


@pytest.mark.parametrize(
    "script, commands, expected_file", _golden_debug_cases("error")
)
def test_공유_fixture_에러_예제의_debug_세션_출력이_기대와_같다(
    script, commands, expected_file, capsys
):
    expected = expected_file.read_text(encoding="utf-8")

    assert run_debug(script, commands, capsys) == expected
