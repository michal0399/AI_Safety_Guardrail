## Cleaning up globally-installed Python packages

These helper scripts detect and optionally uninstall pip packages that appear to be installed globally (system site-packages). They are intentionally conservative and interactive.

Files added:
- `scripts/cleanup_global_python_packages.ps1` — PowerShell script for Windows
- `scripts/cleanup_global_python_packages.sh` — Bash script for macOS/Linux

How they work
- They abort if they detect an active virtual environment.
- They list installed packages and their `Location` reported by `pip show`.
- They apply a heuristic: packages whose `Location` is outside your user profile/home directory are shown as potential global installs.
- You must confirm (`yes`) before the scripts will uninstall anything.

Usage

On Windows (PowerShell):
```powershell
.\scripts\cleanup_global_python_packages.ps1 [-IncludeUser]
```

On Unix/macOS:
```bash
bash scripts/cleanup_global_python_packages.sh [--include-user]
```

If you provide the `-IncludeUser` / `--include-user` flag the scripts will include packages installed under your user profile/home directory in the candidate list (use with care).

Notes & recommendations
- Always review the detected list before uninstalling. Some system packages are required by OS tools.
- Prefer creating per-project virtual environments:
  ```bash
  python -m venv .venv
  .venv\Scripts\Activate.ps1  # Windows PowerShell
  source .venv/bin/activate    # macOS/Linux
  pip install -r requirements.txt
  ```
- For CLI tools that you want globally available, consider `pipx` instead of a global pip install.
