[![codecov](https://codecov.io/gh/kimbyungnam/CodeFab-4/graph/badge.svg?token=SJ40GY81IP)](https://codecov.io/gh/kimbyungnam/CodeFab-4)

# CodeFab-4
CodeFab Interpreter 프로젝트

## Install

가상환경(venv)을 만들고, 그 안에서 설치합니다.

**cmd (Windows)**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install flit
flit install -s
```

**PowerShell (Windows)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install flit
flit install -s
```

**Git Bash / macOS / Linux**
```bash
python -m venv .venv
source .venv/Scripts/activate   # macOS/Linux는 source .venv/bin/activate
python -m pip install flit
flit install -s
```

`flit install -s`를 실행하면 venv 안에 `codefab` 명령어가 설치됩니다. 이후 작업은 venv를
활성화한 상태(프롬프트 앞에 `(.venv)`가 붙은 상태)에서 진행하면 되고, 빠져나올 때는
`deactivate`를 입력합니다.

## How to use

`codefab`은 서브커맨드로 모드를 선택합니다.

### REPL 모드 (인자 없이 실행)

```bash
codefab
```

한 줄씩 입력하면 즉시 실행되고, `exit` 또는 `quit`을 입력하면 종료됩니다.

### 파일 모드 (`run` 서브커맨드)

```bash
codefab run <스크립트경로>
```

## Development

### Test

pytest 를 사용합니다
```bash
pytest tests
```

### pre-commit

pre-commit 설치
```bash
pre-commit install
```

### Commit Convention

This project follows the [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) specification.

Commit messages are validated with [Commitizen](https://commitizen-tools.github.io/commitizen/) and Git hooks are managed by [pre-commit](https://pre-commit.com/).

#### References

- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/)
- [Commitizen Documentation](https://commitizen-tools.github.io/commitizen/)
- [Commitizen - Writing Commits](https://commitizen-tools.github.io/commitizen/tutorials/writing_commits/)
- [pre-commit Documentation](https://pre-commit.com/)

### Branch Convention

작업 성격에 따라서 Branch 이름은 아래와 같이 사용합니다

1. feature : Red 테스트 와 기능 추가 작업
2. test : Test 코드만 추가 작업
3. refactoring : 기능 변경 없이 Refactoring 작업
