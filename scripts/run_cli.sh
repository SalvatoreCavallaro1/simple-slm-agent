#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ -x ".venv/bin/python" ]]; then
  PYTHON_BIN=".venv/bin/python"
elif [[ -x ".venv/Scripts/python.exe" ]]; then
  PYTHON_BIN=".venv/Scripts/python.exe"
else
  PYTHON_BIN="python"
fi

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ".env"
  set +a
fi

PROMPT_VALUE="${PROMPT:-Explain what an API gateway is}"
MODEL_VALUE="${MODEL:-${PRIMARY_MODEL:-phi4-mini}}"

"${PYTHON_BIN}" -m app.cli --prompt "${PROMPT_VALUE}" --model "${MODEL_VALUE}"
