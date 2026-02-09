#!/usr/bin/env bash
set -euo pipefail

# Run pytest in offline/restricted environments by reusing any local site-packages
# that already contains pytest.

if python3 -m pytest --version >/dev/null 2>&1; then
  exec python3 -m pytest "$@"
fi

find_pytest_site_packages() {
  local candidate
  while IFS= read -r candidate; do
    if [[ -f "${candidate}/pytest/__init__.py" || -d "${candidate}/_pytest" ]]; then
      echo "${candidate}"
      return 0
    fi
  done < <(find /home/palmtom -type d -path '*/site-packages' 2>/dev/null)
  return 1
}

if site_packages_path="$(find_pytest_site_packages)"; then
  export PYTHONPATH="${site_packages_path}${PYTHONPATH:+:${PYTHONPATH}}"
  exec python3 -m pytest "$@"
fi

echo "pytest not found locally and no offline site-packages with pytest was discovered." >&2
echo "Please provide a local wheel/cache or allow network installation." >&2
exit 127
