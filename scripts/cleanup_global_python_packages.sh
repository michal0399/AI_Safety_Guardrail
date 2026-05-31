#!/usr/bin/env bash
# Safe helper to detect and optionally uninstall globally-installed pip packages.
# Do not run inside an active virtualenv; the script will abort if it detects one.

set -euo pipefail

# parse args
INCLUDE_USER=0
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    -u|--include-user)
      INCLUDE_USER=1
      shift
      ;;
    -h|--help)
      echo "Usage: $0 [--include-user]"; exit 0
      ;;
    *)
      shift
      ;;
  esac
done

python -V >/dev/null 2>&1 || { echo "Python not found on PATH" >&2; exit 2; }

in_venv=$(python - <<'PY'
import sys
print('1' if sys.prefix != getattr(sys,'base_prefix',sys.prefix) else '0')
PY
)
if [ "$in_venv" = "1" ]; then
  echo "You appear to be inside a virtualenv. Deactivate it before running this script." >&2
  exit 1
fi

pkgs_json=$(python -m pip list --format=json 2>/dev/null) || { echo "Failed to list pip packages" >&2; exit 3; }
pkgs=$(echo "$pkgs_json" | python -c "import sys, json; pkgs=json.load(sys.stdin); import pprint; print('\n'.join([p['name']+','+p['version'] for p in pkgs]))")

echo "Installed packages (first 20):"
echo "$pkgs" | head -n 20

# Build candidate list with locations
candidates=()
while IFS=',' read -r name ver; do
  if [ "$name" = "pip" ] || [ "$name" = "setuptools" ] || [ "$name" = "wheel" ]; then
    continue
  fi
  loc=$(python - <<PY
import sys, subprocess
name='$name'
out = subprocess.run([sys.executable,'-m','pip','show',name], capture_output=True, text=True)
for line in out.stdout.splitlines():
    if line.startswith('Location:'):
        print(line.split(':',1)[1].strip())
        break
PY
)
  if [ -n "$loc" ]; then
    candidates+=("$name::$ver::$loc")
  fi
done <<< "$pkgs"

user_prefix="$HOME"
echo "\nPotential candidate packages:"
for item in "${candidates[@]}"; do
  IFS='::' read -r n v l <<< "$item"
  if [ "$INCLUDE_USER" -eq 1 ] || [[ $l != $user_prefix* ]]; then
    echo "$n $v -> $l"
  fi
done

read -p "Type 'yes' to uninstall the above packages: " confirm
if [ "$confirm" != "yes" ]; then
  echo "Abort. No changes made."
  exit 0
fi

for item in "${candidates[@]}"; do
  IFS='::' read -r n v l <<< "$item"
  if [ "$INCLUDE_USER" -eq 1 ] || [[ $l != $user_prefix* ]]; then
    echo "Uninstalling $n"
    python -m pip uninstall -y "$n" || true
  fi
done

echo "Done. Consider using virtual environments or pipx for CLI tools."
