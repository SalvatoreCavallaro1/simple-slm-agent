$ErrorActionPreference = "Stop"

Invoke-RestMethod https://ollama.com/install.ps1 | Invoke-Expression
ollama --version
