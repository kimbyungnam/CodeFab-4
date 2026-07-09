"""`가져오기`(import) 관련 CLI golden 테스트.

일반 `fixtures/laugh/{normal,error}/<이름>.laugh` + `.out` 관례는 파일 하나로 끝나는
케이스만 다루는데, import 시나리오는 진입점(`main.laugh`)이 다른 `.laugh` 파일을
가져오므로 여러 파일이 필요하다. 그래서 `fixtures/laugh/import/{normal,error}/<시나리오>/`
디렉터리 하나에 진입점 `main.laugh`, 그 파일이 가져오는 나머지 `.laugh` 파일들, 기대
출력 `main.out`을 함께 두고, 시나리오 디렉터리 자체를 glob으로 모아 실행한다.

순환 import 에러 메시지에는 실행 환경마다 달라지는 절대 경로가 들어가므로, golden
파일에는 `<dir>` 자리표시자를 쓰고 비교 전에 시나리오 디렉터리의 실제 절대 경로를 그
자리표시자로 치환한다 (경로 구분자도 `/`로 통일해 OS 간 차이를 없앤다).
"""

from pathlib import Path

import pytest

from tests.integration.test_cli_integration import run_cli

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "laugh" / "import"


def _normalize(text: str, scenario_dir: Path) -> str:
    text = text.replace(str(scenario_dir), "<dir>")
    return text.replace("\\", "/")


def _golden_import_cases(kind: str) -> list[pytest.param]:
    return [
        pytest.param(scenario_dir, id=scenario_dir.name)
        for scenario_dir in sorted((FIXTURES_DIR / kind).iterdir())
        if scenario_dir.is_dir()
    ]


@pytest.mark.parametrize("scenario_dir", _golden_import_cases("normal"))
def test_정상동작_import_golden_예제가_기대한_출력을_내고_종료코드_0을_반환한다(
    scenario_dir,
):
    expected = (scenario_dir / "main.out").read_text(encoding="utf-8")

    result = run_cli(scenario_dir / "main.laugh", cwd=scenario_dir)

    assert _normalize(result.stdout, scenario_dir) == expected
    assert result.returncode == 0


@pytest.mark.parametrize("scenario_dir", _golden_import_cases("error"))
def test_에러_import_golden_예제가_기대한_에러_메시지를_내고_종료코드_1을_반환한다(
    scenario_dir,
):
    expected = (scenario_dir / "main.out").read_text(encoding="utf-8")

    result = run_cli(scenario_dir / "main.laugh", cwd=scenario_dir)

    assert _normalize(result.stdout, scenario_dir) == expected
    assert result.returncode == 1
