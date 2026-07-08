"""codefab CLI(`codefab <file>`) 프로세스에 대한 golden 테스트.

`tests/fixtures/cli/{normal,error}/`에 있는 `.laugh` 소스 파일을 실제로
`python -m codefab.cli <파일>`에 넘겨 실행하고, 같은 이름의 `.out` 파일과 stdout을
바이트 단위로 비교한다. `normal/`은 종료 코드 0, `error/`는 종료 코드 1을 기대한다.

이 fixture들은 테스트케이스.md에 정리된 예제를 그대로 옮긴 것이다. 새 케이스를 추가하려면
`tests/fixtures/cli/<normal|error>/<이름>.laugh`와 `<이름>.out` 한 쌍을 추가하면 된다
(pytest가 자동으로 수집한다).

일부 케이스는 Assembler/Checker의 미구현·버그(`!=` 연산자가 `_equality`에 배선되지 않음,
`정의되지 않은 변수` 참조가 Executor의 런타임 에러가 아닌 Checker의 정적 에러로 먼저
잡히는 문제)로 인해 현재 실패(red)한다 — 알려진 상태이며, 해당 기능이 구현/정정되면
이 테스트들이 통과해야 한다.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "cli"


def run_cli(script: Path, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "codefab.cli", "run", str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=cwd,
        env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
        timeout=10,
    )


def _golden_cases(kind: str) -> list[pytest.param]:
    return [
        pytest.param(script, script.with_suffix(".out"), id=script.stem)
        for script in sorted((FIXTURES_DIR / kind).glob("*.laugh"))
    ]


@pytest.mark.parametrize("script, expected_file", _golden_cases("normal"))
def test_정상동작_golden_예제가_기대한_출력을_내고_종료코드_0을_반환한다(
    script, expected_file
):
    result = run_cli(script)

    assert result.stdout == expected_file.read_text(encoding="utf-8")
    assert result.returncode == 0


@pytest.mark.parametrize("script, expected_file", _golden_cases("error"))
def test_에러_golden_예제가_기대한_에러_메시지를_내고_종료코드_1을_반환한다(
    script, expected_file
):
    result = run_cli(script)

    assert result.stdout == expected_file.read_text(encoding="utf-8")
    assert result.returncode == 1


def test_존재하지_않는_파일이면_파일_오류_메시지를_내고_종료코드_1을_반환한다(tmp_path):
    missing = tmp_path / "없는파일.txt"

    result = run_cli(missing)

    assert "파일 오류" in result.stdout
    assert result.returncode == 1


def test_가져오기로_다른_파일의_변수를_읽어_출력한다(tmp_path):
    (tmp_path / "math.txt").write_text("변수 pi = 3.14;", encoding="utf-8")
    main_script = tmp_path / "main.laugh"
    main_script.write_text(
        '가져오기 "math.txt" 별칭 math;\n출력 math.pi;', encoding="utf-8"
    )

    result = run_cli(main_script, cwd=tmp_path)

    assert result.stdout == "3.14\n"
    assert result.returncode == 0
