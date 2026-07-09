# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

CodeFab-4 is an interpreter for a small Lox-like scripting language ("Laugh Language") whose keywords
are Korean (`변수`, `만약`, `아니면`, `반복`, `출력`, `참`, `거짓`, `그리고`, `또는`). See `docs/language.md`
for the full grammar (EBNF) and AST node reference, and `테스트케이스.md` for example programs (both
normal-case and expected-error scripts) written by the team.

## Commands

```bash
# install (editable, with dev/test extras) — uses flit, not pip install -e
python -m pip install flit
flit install -s

# run all tests
pytest tests

# run a single test file / test
pytest tests/test_checker.py
pytest tests/test_checker.py::test_변수_중복_선언_에러_검출 -v

# lint / format (ruff, no local config — uses ruff defaults)
ruff check .
ruff check --select I --fix .   # isort
ruff format .

# pre-commit (runs the above automatically on commit)
pre-commit install
```

Commit messages must follow Conventional Commits and are enforced by Commitizen via a `commit-msg`
git hook (installed through `pre-commit install`, see `.cz.toml` / `.pre-commit-config.yaml`).

### Branch naming

Branch names encode the kind of work being done: `feature/*` (red test + new functionality),
`test/*` (test-only additions), `refactoring/*` (no behavior change).

## Architecture

The interpreter pipeline is **Assembler Unit → Checker Unit → Executor Unit**, matching the module
layout:

- `codefab/tokenizer.py`, `codefab/tokens.py` — lexing. `Tokenizer.scan_tokens()` turns source text
  into a `list[Token]`. `KEYWORDS` maps both English and Korean surface spellings to the same
  `TokenType` (e.g. `"var"` and `"변수"` both produce `TokenType.VAR`) — only the keyword's lexeme is
  localized, not the enum member names or operator symbols.
- `codefab/assembler/` — Assembler Unit. `ExpressionParser` (in `expression_parser.py`) implements the
  precedence-climbing grammar from `docs/language.md` (`assignment → logic_or → logic_and → equality →
  comparison → term → factor → unary → primary`) and builds `Expr` nodes. `StatementParser` (in
  `statement_parser.py`) parses top-level statements and blocks. `Assembler` (in `assembler.py`) drives
  these parsers to produce the final AST.
- `codefab/checker.py` — Checker Unit. Static pre-execution pass (`Checker.resolve`) that walks the AST
  via the visitor pattern (`node.accept(self)`) to catch: use of an undeclared variable, duplicate
  declaration in the same scope, and self-reference during a variable's own initializer
  (`변수 a = a;`).
- `codefab/executor_unit.py` — Executor Unit. `ExecutorUnit.execute` walks the AST (statements and
  expressions) via the visitor pattern, using a flat `dict` environment for variable storage. Runtime
  failures raise `ExecutorRuntimeError(message, line)` with team-specified Korean error messages
  (e.g. `"0으로 나눈 오류"`, `"피연산자는 반드시 숫자여야 합니다."`) — when adding new runtime checks,
  match this message style and always attach the offending line number.
- `codefab/app/repl.py` — Interactive REPL. `Repl` class handles multi-line input, incomplete code
  detection, and special logic for if/else statements; `main()` entry point runs it over stdin.

### AST node hierarchy

All `Expr` and `Stmt` classes are defined in `codefab/ast_nodes.py` as a single visitor-pattern
hierarchy: `Expr` and `Stmt` are abstract base classes with an abstract `accept(self, visitor)` method
(e.g. `Binary.accept` calls `visitor.visit_binary(self)`). Every module in the pipeline
(`expression_parser.py`, `statement_parser.py`, `checker.py`, `executor_unit.py`) imports from
`ast_nodes.py` and uses the visitor pattern consistently.

### Testing conventions

- Tests use `pytest` with `pytest-mock` (`mocker` fixture). `test_checker.py` builds AST nodes as
  `mocker.Mock()` objects with `.accept.side_effect` wired to the real `visit_*` method, rather than
  instantiating real `ast_nodes` classes — follow this pattern for new Checker tests.
- `test_executor_unit.py` and `test_expression_parser.py` construct real node instances directly (no
  tokenizer/parser round-trip) to isolate the unit under test.
- Test names are Korean, describing the scenario under test (e.g.
  `test_변수_중복_선언_에러_검출`, "detects duplicate variable declaration error").
