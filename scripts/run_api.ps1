$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root ".env"
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$pythonBin = if (Test-Path $venvPython) { $venvPython } else { "python" }

function Normalize-EnvValue {
    param([string]$Value)

    $trimmed = $Value.Trim()
    if ($trimmed.Length -ge 2) {
        $first = $trimmed.Substring(0, 1)
        $last = $trimmed.Substring($trimmed.Length - 1, 1)
        if (($first -eq '"' -or $first -eq "'") -and $first -eq $last) {
            return $trimmed.Substring(1, $trimmed.Length - 2).Trim()
        }
    }

    return $trimmed
}

if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ([string]::IsNullOrWhiteSpace($_) -or $_.TrimStart().StartsWith("#")) {
            return
        }

        $name, $value = $_ -split "=", 2
        if ($null -ne $name -and $null -ne $value) {
            [Environment]::SetEnvironmentVariable($name.Trim(), (Normalize-EnvValue $value), "Process")
        }
    }
}

& $pythonBin -m uvicorn app.api:app --host 127.0.0.1 --port 8000
