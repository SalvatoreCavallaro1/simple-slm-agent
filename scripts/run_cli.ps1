param(
    [string]$Prompt = "Explain what an API gateway is",
    [string]$Model = ""
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root ".env"
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$pythonBin = if (Test-Path $venvPython) { $venvPython } else { "python" }

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ([string]::IsNullOrWhiteSpace($_) -or $_.TrimStart().StartsWith("#")) {
            return
        }

        $name, $value = $_ -split "=", 2
        if ($null -ne $name -and $null -ne $value) {
            [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), "Process")
        }
    }
}

if ([string]::IsNullOrWhiteSpace($Model)) {
    $Model = if (-not [string]::IsNullOrWhiteSpace($env:MODEL)) { $env:MODEL } else { $env:PRIMARY_MODEL }
}

& $pythonBin -m app.cli --prompt $Prompt --model $Model
