---
description: Run code quality checks (lint, mypy, tests) for this project
---

# Code Quality Checks

This project uses **poetry** for dependency management. **DO NOT use uv**.

## Prerequisites

Activate the virtual environment first:

```bash
cd /home/hatch/projects/cep/simt-emlite
. .venv/bin/activate
```

## Run All Checks

// turbo

1. Run lint:

```bash
poetry run lint
```

Or use the bin script:

```bash
bin/lint
```

// turbo
2. Run mypy for type checking:

```bash
poetry run mypy simt_emlite/
```

// turbo
3. Run all tests (uses unittest, not pytest):

```bash
poetry run test
```

Or use the bin script:

```bash
bin/test
```

## Check a Single File

// turbo
4. Type check a specific file:

```bash
poetry run mypy simt_emlite/path/to/file.py
```

// turbo
5. Run a single test file:

```bash
python -m unittest tests/path/to/test_file.py
```

## Quick Syntax Check

// turbo
6. Verify Python syntax without running full mypy:

```bash
python3 -m py_compile simt_emlite/path/to/file.py
```

## Format Code

// turbo
7. Run Ruff formatter/linter:

```bash
ruff check simt_emlite/
```

## All Checks Script

// turbo
8. Run all checks at once:

```bash
bin/all-checks
```

## Important Notes

- **Poetry only**: This project is NOT configured for uv
- **unittest only**: Do NOT use pytest
- **Activate venv**: Always activate `.venv` before running commands
