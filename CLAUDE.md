# simt-emlite

## Testing & Linting

- Run tests: `poetry run test` (uses unittest, NOT pytest)
- Run linter: `poetry run lint`
- Always run both after making changes
- If poetry is not available, activate venv and use: `source .venv/bin/activate && python -c "from simt_emlite import run_tests; run_tests()"`
