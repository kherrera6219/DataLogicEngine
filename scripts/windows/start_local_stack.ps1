[CmdletBinding()]
Param(
    [switch]$SkipPrecheck,
    [switch]$SkipMigrations,
    [switch]$NoFrontend
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$PythonPath = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$FrontendDir = Join-Path $RepoRoot "frontend"
$EnvFile = Join-Path $RepoRoot ".env"
$PidDir = Join-Path $RepoRoot "logs"
$PidFile = Join-Path $PidDir "local_stack.pids.json"

function Write-Step([string]$Message, [string]$Color = "Cyan") {
    Write-Host $Message -ForegroundColor $Color
}

function Assert-Path([string]$Path, [string]$Message) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw $Message
    }
}

function Get-EnvMap([string]$Path) {
    $map = @{}
    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) {
            continue
        }
        $index = $trimmed.IndexOf("=")
        if ($index -lt 1) {
            continue
        }
        $key = $trimmed.Substring(0, $index).Trim()
        $value = $trimmed.Substring($index + 1).Trim()
        $map[$key] = $value
    }
    return $map
}

function Wait-HttpEndpoint([string]$Url, [int]$MaxAttempts = 30) {
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        try {
            Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2 | Out-Null
            return $true
        }
        catch {
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

function Test-PortOpen([int]$Port) {
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $async = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        $connected = $async.AsyncWaitHandle.WaitOne(500, $false)
        if ($connected -and $client.Connected) {
            $client.EndConnect($async)
            return $true
        }
        return $false
    }
    catch {
        return $false
    }
    finally {
        $client.Close()
    }
}

Assert-Path $PythonPath "Python virtual environment not found at $PythonPath. Run scripts/dev_setup.py first."
Assert-Path $EnvFile ".env not found at $EnvFile. Copy .env.template to .env and configure it."

$envMap = Get-EnvMap -Path $EnvFile
if (-not $envMap["SESSION_SECRET"]) {
    throw "SESSION_SECRET missing in .env. Generate one before startup."
}

$providerKeys = @(
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "MISTRAL_API_KEY"
)
$providerConfigured = $false
foreach ($key in $providerKeys) {
    if ($envMap[$key]) {
        $providerConfigured = $true
        break
    }
}
if (-not $providerConfigured) {
    throw "No provider API key configured in .env. Set at least one LLM provider key."
}

if (-not $SkipPrecheck) {
    Write-Step "Running runtime precheck..."
    & $PythonPath (Join-Path $RepoRoot "scripts\runtime_precheck.py")
    if ($LASTEXITCODE -ne 0) {
        throw "runtime_precheck.py reported blockers."
    }
}

if (-not $SkipMigrations) {
    Write-Step "Applying database migrations..."
    & $PythonPath -m flask --app app.py db upgrade
    if ($LASTEXITCODE -ne 0) {
        Write-Step "Migration failed. Attempting local recovery with Alembic stamp..." "Yellow"
        & $PythonPath -m flask --app app.py db stamp head
        if ($LASTEXITCODE -ne 0) {
            throw "Database migration failed and recovery stamp failed."
        }
        Write-Step "Migration recovery completed (stamped head)." "Yellow"
    }
}

if (-not (Test-Path -LiteralPath $PidDir)) {
    New-Item -ItemType Directory -Path $PidDir | Out-Null
}

# Local defaults for HTTP development
$env:FLASK_ENV = "development"
$env:PORT = "5000"
$env:USE_REDIS = "false"
$env:SESSION_COOKIE_SECURE = "false"

Write-Step "Starting backend on http://127.0.0.1:5000 ..."
$backendProcess = Start-Process -FilePath $PythonPath -ArgumentList "app.py" -WorkingDirectory $RepoRoot -PassThru

if (-not (Wait-HttpEndpoint -Url "http://127.0.0.1:5000/health")) {
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    throw "Backend did not become healthy at /health within timeout."
}
Write-Step "Backend is healthy." "Green"

$frontendProcess = $null
if (-not $NoFrontend) {
    Assert-Path (Join-Path $FrontendDir "node_modules") "Frontend dependencies missing. Run: cd frontend; npm install"
    Write-Step "Starting frontend on http://127.0.0.1:3000 ..."
    $frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm run dev -- --hostname 127.0.0.1 --port 3000" -WorkingDirectory $FrontendDir -PassThru

    $frontendReady = $false
    for ($i = 1; $i -le 180; $i++) {
        if ($frontendProcess.HasExited) {
            break
        }
        if (Test-PortOpen -Port 3000) {
            $frontendReady = $true
            break
        }
        Start-Sleep -Seconds 1
    }

    if (-not $frontendReady) {
        Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
        $exitCode = $frontendProcess.ExitCode
        throw "Frontend did not respond on port 3000 within timeout. ExitCode=$exitCode"
    }
    Write-Step "Frontend port 3000 is open." "Green"
}

$pidRecord = @{
    started_at = (Get-Date).ToString("o")
    backend_pid = $backendProcess.Id
    frontend_pid = if ($frontendProcess) { $frontendProcess.Id } else { $null }
}
$pidRecord | ConvertTo-Json | Set-Content -LiteralPath $PidFile -Encoding UTF8

Write-Step "Stack started successfully." "Green"
Write-Host "Backend:  http://127.0.0.1:5000"
if ($frontendProcess) {
    Write-Host "Frontend: http://127.0.0.1:3000"
}
Write-Host "PID file: $PidFile"
Write-Host "Stop command: .\\scripts\\windows\\stop_local_stack.ps1"
