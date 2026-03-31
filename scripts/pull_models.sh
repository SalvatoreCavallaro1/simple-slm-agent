#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/.env"
  set +a
fi

MODELS="${AVAILABLE_MODELS:-phi4-mini,qwen3:4b,llama3.2:3b}"
IFS=',' read -r -a MODEL_ARRAY <<< "${MODELS}"

for model in "${MODEL_ARRAY[@]}"; do
  trimmed_model="$(echo "${model}" | xargs)"
  if [[ -z "${trimmed_model}" ]]; then
    continue
  fi

  echo "Pulling ${trimmed_model}"
  ollama pull "${trimmed_model}"
done
