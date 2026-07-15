Param(
    [string]$RepoRoot
)

$ErrorActionPreference = "Stop"

$FrontendRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $FrontendRoot "..")).Path
}

$PythonCandidates = @(
    $env:DLE_BACKEND_BUILD_PYTHON,
    (Join-Path $RepoRoot ".venv311\Scripts\python.exe"),
    (Join-Path $RepoRoot ".venv\Scripts\python.exe")
) | Where-Object { $_ }

$BackendPython = $null
foreach ($Candidate in $PythonCandidates) {
    if (Test-Path $Candidate) {
        $BackendPython = $Candidate
        break
    }
}

if (-not $BackendPython) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        $BackendPython = $PythonCommand.Source
    }
}

if (-not $BackendPython) {
    throw "No Python executable found for backend build."
}

Write-Host "Rebuilding Python backend for installer with: $BackendPython" -ForegroundColor Cyan

Push-Location $RepoRoot
try {
    & $BackendPython scripts\build_backend.py
    if ($LASTEXITCODE -ne 0) {
        throw "Backend build failed with exit code $LASTEXITCODE."
    }

    $BackendExe = Join-Path $RepoRoot "dist\DataLogic_Backend\DataLogic_Backend.exe"
    if (-not (Test-Path $BackendExe)) {
        throw "Backend executable was not produced at $BackendExe."
    }
}
finally {
    Pop-Location
}

Write-Host "Backend rebuilt for installer packaging." -ForegroundColor Green
