$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$venvDir = Join-Path $root ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    python -m venv $venvDir
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $root "requirements.txt")
& $venvPython -m pip install -e $root

Write-Host "Setup complete. Virtual environment: $venvDir"
