#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

if [[ ! -f ".env" ]]; then
  echo "Missing .env in $REPO_ROOT"
  echo "Copy .env.example to .env and fill the local BYOK values first."
  exit 1
fi

if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON_CMD=("${PYTHON_BIN}")
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD=("python3")
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD=("python")
else
  echo "Python was not found."
  echo "Install Python 3.11+ and try again."
  exit 1
fi

if ! "${PYTHON_CMD[@]}" -c "import httpx, dotenv, swarmrepo_sdk" >/dev/null 2>&1; then
  echo "Missing Python dependencies for swarmrepo-agent-runtime."
  echo "For private-repo validation, install specs, SDK, and runtime first:"
  echo "  ${PYTHON_CMD[*]} -m pip install -e /path/to/swarmrepo-specs"
  echo "  ${PYTHON_CMD[*]} -m pip install -e /path/to/swarmrepo-sdk"
  echo "  ${PYTHON_CMD[*]} -m pip install -e ."
  exit 1
fi

export PYTHONPATH="$REPO_ROOT/src${PYTHONPATH:+:$PYTHONPATH}"

echo "Starting SwarmRepo custom agent template from $REPO_ROOT"
exec "${PYTHON_CMD[@]}" -m swarmrepo_agent_runtime.custom_agent_template
