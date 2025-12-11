# SIMT-EMLITE Development Guide

## Commands

- Install: `poetry install`
- Run all tests: `poetry run test` or `bin/test`
- Run single test: `python -m unittest tests/simt_emlite/sync/test_syncer_base.py`
- Lint: `poetry run lint` or `bin/lint`
- Build: `poetry build`
- Publish: `poetry publish --build -r test-pypi`
- gRPC code generation: `cd simt_emlite/mediator/grpc && python grpc_codegen.py`

## Python

Poetry is used to manage dependencies and run scripts.

Activate the .venv before running python.

Write unit tests with `unittest`. See existing tests under `tests` and follow a similar layout and style.

## Shell Scripting

- Use `/bin/sh` POSIX shell only for maximum compatibility
- Use `. ./script.sh` instead of `source script.sh` to source files (`.` is POSIX-compliant, `source` is bash-specific)

## Code Style

- Python 3.13+ with type hints required
- snake_case for variables/functions, PascalCase for classes
- Imports: stdlib first, third-party second, local imports last
- Use absolute imports from root (e.g., `from simt_emlite.util.logging import get_logger`)
- 4-space indentation, ~100 char line length
- Docstrings using triple quotes
- Use structlog for logging with binding context
- Use ABC for abstract classes, implement with @abstractmethod
- Exception handling: specific catches first, general last with detailed logging
- Format with Ruff (`ruff check` - configured in pyproject.toml)
