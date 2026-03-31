#!/usr/bin/env bash
set -euo pipefail

curl -fsSL https://ollama.com/install.sh | sh
command -v ollama >/dev/null 2>&1
ollama --version
