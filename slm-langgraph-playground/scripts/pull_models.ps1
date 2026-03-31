$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root ".env"

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

$models = $env:AVAILABLE_MODELS
if ([string]::IsNullOrWhiteSpace($models)) {
    $models = "phi4-mini,qwen3:4b,llama3.2:3b"
}

$models.Split(",") | ForEach-Object {
    $model = $_.Trim()
    if (-not [string]::IsNullOrWhiteSpace($model)) {
        Write-Host "Pulling $model"
        ollama pull $model
    }
}
