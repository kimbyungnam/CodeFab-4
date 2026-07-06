# CodeFab-4
CodeFab Interpreter 프로젝트

## Install
```bash
python -m pip install flit
flit install -s
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
