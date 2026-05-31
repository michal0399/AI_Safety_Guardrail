"""Run API key tests with the project venv when available (GitHub Desktop safe)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTEST_ARGS = ["tests/test_api_keys.py", "-v", "--tb=short"]


def _venv_site_packages() -> Path | None:
    venv = ROOT / ".venv"
    if sys.platform == "win32":
        candidate = venv / "Lib" / "site-packages"
    else:
        lib = venv / "lib"
        if not lib.is_dir():
            return None
        matches = list(lib.glob("python*/site-packages"))
        candidate = matches[0] if len(matches) == 1 else None
    return candidate if candidate and candidate.is_dir() else None


def _bootstrap_import_path() -> None:
    os.chdir(ROOT)
    for path in (ROOT / "src", _venv_site_packages()):
        if path is None:
            continue
        path_str = str(path)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)


def main() -> int:
    _bootstrap_import_path()
    import pytest

    return pytest.main(PYTEST_ARGS)


if __name__ == "__main__":
    raise SystemExit(main())
