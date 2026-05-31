# Contributing to Safety Guardrail

Thank you for your interest in contributing. This guide covers local setup, development workflow, and what we expect in pull requests.

## Prerequisites

- Python 3.13+
- Git
- Optional: Docker and Redis (for full API key and vault testing)

## Local setup

```bash
git clone <repo-url>
cd Safety_Guardrail

# Recommended: use the project virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS / Linux

pip install -e .
pip install -r requirements.txt
pre-commit install
```

Copy environment variables and adjust as needed:

```bash
cp .env.example .env
```

See [API keys](API_KEYS.md) and the root [README](../README.md) for required variables.

## Development workflow

1. Create a branch from `master`:

   ```bash
   git checkout -b feature/short-description
   ```

2. Make focused changes. Keep diffs small and scoped to one concern when possible.

3. Run tests locally:

   ```bash
   # Fast default (mock judge, no external API calls)
   pytest tests/ -v

   # API key tests (also run by pre-commit)
   pytest tests/test_api_keys.py -v

   # Optional: security and integration with real judge
   USE_REAL_JUDGE=1 pytest tests/security tests/integration -v
   ```

4. Run pre-commit before committing:

   ```bash
   pre-commit run --all-files
   ```

5. Commit with a clear message (e.g. `feat:`, `fix:`, `docs:`, `test:`, `refactor:`).

6. Open a pull request against `master` with:
   - What changed and why
   - How you tested it
   - Any docs updates included

## Code standards

| Tool | Purpose |
|------|---------|
| **black** | Formatting (120 char line length) |
| **isort** | Import sorting (black profile) |
| **bandit** | Security linting on `src/` |
| **pytest** | Unit and integration tests |
| **safety** | Dependency vulnerability check |

Pre-commit runs these automatically on commit. Fix hook failures rather than skipping hooks.

### Python conventions

- Match existing patterns in `src/safety_guardrail/`.
- Prefer clear names and minimal scope; avoid drive-by refactors.
- Add docstrings for non-obvious public APIs.
- Do not commit secrets, API keys, or `.env` files.

### Tests

- Place tests in the appropriate directory under `tests/` (see [Test structure](TEST_STRUCTURE.md)).
- Use fixtures from `tests/conftest.py` where possible.
- Add or update tests for behavior changes and bug fixes.
- Security-sensitive changes should include tests under `tests/security/`.

## Pull request checklist

- [ ] Tests pass: `pytest tests/ -v`
- [ ] Pre-commit passes: `pre-commit run --all-files`
- [ ] New behavior is documented in `docs/` when user-facing
- [ ] No credentials or personal data in code, logs, or commits
- [ ] PR description explains the change and test plan

## Reporting issues

When filing an issue, include:

- Python version and OS
- Steps to reproduce
- Expected vs actual behavior
- Relevant log excerpts from `logs/` (redact PII first)

## Security

This project handles PII locally before external API calls. If you find a security issue, do not open a public issue with exploit details until maintainers can respond. Describe impact and reproduction steps responsibly.

## Questions

- [Testing guide](TESTING.md)
- [Logging](LOGGING.md)
- [Mock judge setup](MOCK_JUDGE.md)
