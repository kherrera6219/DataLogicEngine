[CmdletBinding()]
Param(
    [switch]$SkipPrecheck,
    [switch]$SkipMigrations,
    [switch]$NoFrontend,
    [switch]$SkipRouteSmoke,
    [switch]$WithDataServices,
    [int]$BackendPort = 5000,
    [int]$FrontendPort = 3000,
    [bool]$AutoResolvePortConflicts = $true
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

function Get-DockerContainerByPublishedPort([int]$Port) {
    $dockerPath = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $dockerPath) {
        return $null
    }

    $rows = docker ps --format "{{.ID}}|{{.Ports}}" 2>$null
    foreach ($row in $rows) {
        if (-not $row) {
            continue
        }
        $parts = $row -split "\|", 2
        if ($parts.Count -lt 2) {
            continue
        }
        $ports = $parts[1]
        if (
            $ports -match "(^|, )0\.0\.0\.0:$Port->" -or
            $ports -match "(^|, )\[\:\:\]:$Port->" -or
            $ports -match ":$Port->"
        ) {
            return $parts[0]
        }
    }

    return $null
}

function Get-DockerContainerByName([string]$Name) {
    # Exact-name match among running containers. DataLogicEngine's compose pins
    # container_name (ukg-db / ukg-neo4j / ukg-minio / ukg-redis), so this finds
    # *our* container regardless of which host port it ended up on.
    $dockerPath = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $dockerPath) {
        return $null
    }

    $id = docker ps --filter "name=^/$Name$" --format "{{.ID}}" 2>$null | Select-Object -First 1
    if ($id) {
        return $id.Trim()
    }
    return $null
}

function Resolve-DataServiceContainer([string]$PreferredName, [int]$Port) {
    # Prefer DataLogicEngine's OWN named container (ukg-*) so we never adopt a
    # *different* application's container that merely happens to publish the same
    # standard port (e.g. an unrelated Postgres squatting 5432). Only when our
    # named container is absent do we fall back to the port-based lookup — and
    # then we warn loudly if the port owner is a foreign (non-ukg-) container,
    # because reusing its credentials silently couples us to another app's data.
    $byName = Get-DockerContainerByName -Name $PreferredName
    if ($byName) {
        return $byName
    }

    $byPort = Get-DockerContainerByPublishedPort -Port $Port
    if ($byPort) {
        $foreignName = docker inspect -f "{{.Name}}" $byPort 2>$null
        if ($foreignName) {
            $foreignName = $foreignName.TrimStart("/")
        }
        if ($foreignName -and -not $foreignName.StartsWith("ukg-")) {
            Write-Step "WARNING: port $Port is owned by container '$foreignName', not DataLogicEngine's '$PreferredName'. Reusing its credentials — start DataLogicEngine's own stack (or free the port) to avoid coupling to another app." "Yellow"
        }
        return $byPort
    }
    return $null
}

function Get-DockerEnvMap([string]$ContainerId) {
    $map = @{}
    if (-not $ContainerId) {
        return $map
    }

    $lines = docker inspect -f "{{range .Config.Env}}{{println .}}{{end}}" $ContainerId 2>$null
    foreach ($line in $lines) {
        if (-not $line) {
            continue
        }
        $idx = $line.IndexOf("=")
        if ($idx -lt 1) {
            continue
        }
        $key = $line.Substring(0, $idx).Trim()
        $value = $line.Substring($idx + 1).Trim()
        $map[$key] = $value
    }

    return $map
}

function Get-FirstNonEmptyValue([string[]]$Values, [string]$Fallback = "") {
    foreach ($value in $Values) {
        if ($null -ne $value -and $value.Trim().Length -gt 0) {
            return $value.Trim()
        }
    }
    return $Fallback
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

function Wait-PortOpen([int]$Port, [int]$MaxAttempts = 40) {
    for ($i = 1; $i -le $MaxAttempts; $i++) {
        if (Test-PortOpen -Port $Port) {
            return $true
        }
        Start-Sleep -Seconds 1
    }
    return $false
}

function Resolve-RequestedPort(
    [int]$RequestedPort,
    [string]$ServiceName,
    [bool]$AllowAutoResolve,
    [int]$MaxOffset = 40
) {
    if (-not (Test-PortOpen -Port $RequestedPort)) {
        return $RequestedPort
    }

    if (-not $AllowAutoResolve) {
        throw "$ServiceName port $RequestedPort is already in use. Re-run with a different port or -AutoResolvePortConflicts `$true."
    }

    for ($candidate = $RequestedPort + 1; $candidate -le ($RequestedPort + $MaxOffset); $candidate++) {
        if (-not (Test-PortOpen -Port $candidate)) {
            Write-Step "$ServiceName port $RequestedPort is busy. Auto-resolved to port $candidate." "Yellow"
            return $candidate
        }
    }

    throw "Unable to auto-resolve a free port for $ServiceName in range $RequestedPort-$($RequestedPort + $MaxOffset)."
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
    "anthropic_API_KEY",
    "AZURE_OPENAI_API_KEY",
    "GOOGLE_API_KEY",
    "GEMINI_API_KEY",
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

$BackendPort = Resolve-RequestedPort -RequestedPort $BackendPort -ServiceName "Backend" -AllowAutoResolve $AutoResolvePortConflicts
$FrontendPort = Resolve-RequestedPort -RequestedPort $FrontendPort -ServiceName "Frontend" -AllowAutoResolve $AutoResolvePortConflicts

if ($FrontendPort -eq $BackendPort) {
    if (-not $AutoResolvePortConflicts) {
        throw "Backend and frontend ports cannot be the same ($BackendPort)."
    }
    $FrontendPort = Resolve-RequestedPort -RequestedPort ($FrontendPort + 1) -ServiceName "Frontend" -AllowAutoResolve $true
}

if ($WithDataServices) {
    # Key the reuse-vs-start decision on whether DataLogicEngine's OWN containers
    # (ukg-*) are running — NOT on bare port-busy checks. A different app squatting
    # the standard ports (e.g. an unrelated Postgres on 5432) must not be mistaken
    # for our stack and silently reused.
    $ownContainers = [ordered]@{
        "ukg-db"    = 5432
        "ukg-redis" = 6379
        "ukg-neo4j" = 7687
        "ukg-minio" = 9000
    }

    $runningOwn = @()
    $foreignBusy = @()
    foreach ($name in $ownContainers.Keys) {
        if (Get-DockerContainerByName -Name $name) {
            $runningOwn += $name
        }
        elseif (Test-PortOpen -Port $ownContainers[$name]) {
            $owner = Get-DockerContainerByPublishedPort -Port $ownContainers[$name]
            $ownerName = if ($owner) { (docker inspect -f "{{.Name}}" $owner 2>$null).TrimStart("/") } else { "?" }
            $foreignBusy += "$($ownContainers[$name]) -> '$ownerName'"
        }
    }

    if ($runningOwn.Count -eq $ownContainers.Count) {
        Write-Step "DataLogicEngine data containers already running ($($runningOwn -join ', ')). Reusing them." "Yellow"
    }
    else {
        if ($foreignBusy.Count -gt 0) {
            Write-Step "WARNING: standard data-service ports are held by other apps' containers ($($foreignBusy -join ', ')). DataLogicEngine's own containers cannot bind those ports — stop the other stack or free the ports." "Yellow"
        }
        Write-Step "Starting DataLogicEngine data services (ukg-db / ukg-redis / ukg-neo4j / ukg-minio) via docker compose..."
        $dockerPath = Get-Command docker -ErrorAction SilentlyContinue
        if (-not $dockerPath) {
            throw "Docker is required for -WithDataServices but was not found in PATH."
        }

        Push-Location $RepoRoot
        try {
            docker compose up -d db redis neo4j minio | Out-Null
            if ($LASTEXITCODE -ne 0) {
                throw "docker compose failed while starting data services (a standard port may be held by another app's container)."
            }
        }
        finally {
            Pop-Location
        }
    }

    if (-not (Wait-PortOpen -Port 5432)) { throw "PostgreSQL did not open on port 5432." }
    if (-not (Wait-PortOpen -Port 6379)) { throw "Redis did not open on port 6379." }
    if (-not (Wait-PortOpen -Port 7687)) { throw "Neo4j did not open on port 7687." }
    if (-not (Wait-PortOpen -Port 9000)) { throw "MinIO did not open on port 9000." }
    Write-Step "Local data services are reachable." "Green"

    # Defaults from repository compose profile.
    $pgUser = "postgres"
    $pgPassword = "postgres"
    $pgDatabase = "ukg_db"
    $neo4jUser = "neo4j"
    $neo4jPassword = "neo4jpassword"
    $objectAccessKey = "minioadmin"
    $objectSecretKey = "minioadmin123"

    # Discover credentials from DataLogicEngine's own data containers (by name,
    # falling back to port only if our named container isn't running).
    $postgresContainer = Resolve-DataServiceContainer -PreferredName "ukg-db" -Port 5432
    if ($postgresContainer) {
        $pgEnv = Get-DockerEnvMap -ContainerId $postgresContainer
        $pgUser = Get-FirstNonEmptyValue @($pgEnv["POSTGRES_USER"], $pgUser) $pgUser
        $pgPassword = Get-FirstNonEmptyValue @($pgEnv["POSTGRES_PASSWORD"], $pgPassword) $pgPassword
        $pgDatabase = Get-FirstNonEmptyValue @($pgEnv["POSTGRES_DB"], $pgDatabase) $pgDatabase
    }

    $neo4jContainer = Resolve-DataServiceContainer -PreferredName "ukg-neo4j" -Port 7687
    if ($neo4jContainer) {
        $neo4jEnv = Get-DockerEnvMap -ContainerId $neo4jContainer
        $neo4jUser = Get-FirstNonEmptyValue @($neo4jEnv["NEO4J_USER"], $neo4jUser) $neo4jUser
        $neo4jPassword = Get-FirstNonEmptyValue @($neo4jEnv["NEO4J_PASSWORD"], $neo4jPassword) $neo4jPassword
        $neo4jAuth = $neo4jEnv["NEO4J_AUTH"]
        if ($neo4jAuth -and ($neo4jAuth -ne "none") -and $neo4jAuth.Contains("/")) {
            $parts = $neo4jAuth.Split("/", 2)
            if ($parts.Count -eq 2) {
                $neo4jUser = Get-FirstNonEmptyValue @($parts[0], $neo4jUser) $neo4jUser
                $neo4jPassword = Get-FirstNonEmptyValue @($parts[1], $neo4jPassword) $neo4jPassword
            }
        }
    }

    $minioContainer = Resolve-DataServiceContainer -PreferredName "ukg-minio" -Port 9000
    if ($minioContainer) {
        $minioEnv = Get-DockerEnvMap -ContainerId $minioContainer
        $objectAccessKey = Get-FirstNonEmptyValue @($minioEnv["MINIO_ROOT_USER"], $minioEnv["MINIO_ACCESS_KEY"], $objectAccessKey) $objectAccessKey
        $objectSecretKey = Get-FirstNonEmptyValue @($minioEnv["MINIO_ROOT_PASSWORD"], $minioEnv["MINIO_SECRET_KEY"], $objectSecretKey) $objectSecretKey
    }

    $databaseUrlFromProcess = $env:DATABASE_URL
    $databaseUrlFromEnv = $envMap["DATABASE_URL"]
    if ($databaseUrlFromProcess -and $databaseUrlFromProcess.StartsWith("postgres")) {
        $env:DATABASE_URL = $databaseUrlFromProcess
    }
    elseif (-not $databaseUrlFromEnv -or $databaseUrlFromEnv.StartsWith("sqlite")) {
        $env:DATABASE_URL = "postgresql://${pgUser}:${pgPassword}@127.0.0.1:5432/${pgDatabase}"
    }
    else {
        $env:DATABASE_URL = $databaseUrlFromEnv
    }

    # Use isolated DB indexes by default to avoid collisions with pre-existing local Redis data.
    $env:REDIS_URL = Get-FirstNonEmptyValue @($env:REDIS_URL, $envMap["REDIS_URL"], "redis://127.0.0.1:6379/10") "redis://127.0.0.1:6379/10"
    $env:RATELIMIT_STORAGE_URI = Get-FirstNonEmptyValue @($env:RATELIMIT_STORAGE_URI, $envMap["RATELIMIT_STORAGE_URI"], "redis://127.0.0.1:6379/11") "redis://127.0.0.1:6379/11"
    $env:CELERY_BROKER_URL = Get-FirstNonEmptyValue @($env:CELERY_BROKER_URL, $envMap["CELERY_BROKER_URL"], "redis://127.0.0.1:6379/12") "redis://127.0.0.1:6379/12"
    $env:CELERY_RESULT_BACKEND = Get-FirstNonEmptyValue @($env:CELERY_RESULT_BACKEND, $envMap["CELERY_RESULT_BACKEND"], "redis://127.0.0.1:6379/13") "redis://127.0.0.1:6379/13"

    $env:NEO4J_URI = Get-FirstNonEmptyValue @($env:NEO4J_URI, $envMap["NEO4J_URI"], "bolt://127.0.0.1:7687") "bolt://127.0.0.1:7687"
    $env:NEO4J_USER = Get-FirstNonEmptyValue @($env:NEO4J_USER, $envMap["NEO4J_USER"], $neo4jUser) $neo4jUser
    $env:NEO4J_PASSWORD = Get-FirstNonEmptyValue @($env:NEO4J_PASSWORD, $envMap["NEO4J_PASSWORD"], $neo4jPassword) $neo4jPassword

    $env:OBJECT_ENDPOINT_URL = Get-FirstNonEmptyValue @($env:OBJECT_ENDPOINT_URL, $envMap["OBJECT_ENDPOINT_URL"], "http://127.0.0.1:9000") "http://127.0.0.1:9000"
    $env:OBJECT_ACCESS_KEY = Get-FirstNonEmptyValue @($env:OBJECT_ACCESS_KEY, $envMap["OBJECT_ACCESS_KEY"], $objectAccessKey) $objectAccessKey
    $env:OBJECT_SECRET_KEY = Get-FirstNonEmptyValue @($env:OBJECT_SECRET_KEY, $envMap["OBJECT_SECRET_KEY"], $objectSecretKey) $objectSecretKey
    $env:OBJECT_BUCKET = Get-FirstNonEmptyValue @($env:OBJECT_BUCKET, $envMap["OBJECT_BUCKET"], "datalogic") "datalogic"
    $env:POSTGRES_USER = $pgUser
    $env:POSTGRES_PASSWORD = $pgPassword
    $env:POSTGRES_DB = $pgDatabase
    $env:USE_REDIS = "true"
}

if (-not $SkipPrecheck) {
    $env:BACKEND_PORT = "$BackendPort"
    $env:FRONTEND_PORT = "$FrontendPort"
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
        $dbUrl = ""
        if ($env:DATABASE_URL) {
            $dbUrl = "$($env:DATABASE_URL)"
        }
        elseif ($envMap["DATABASE_URL"]) {
            $dbUrl = "$($envMap["DATABASE_URL"])"
        }
        $dbUrlLower = $dbUrl.ToLowerInvariant()
        $isSqlite = $dbUrlLower.StartsWith("sqlite")
        $allowStampFallback = "$($env:UKG_ALLOW_ALEMBIC_STAMP_FALLBACK)".ToLowerInvariant() -eq "true"

        if ($isSqlite -or $allowStampFallback) {
            Write-Step "Migration failed. Attempting local recovery with Alembic stamp..." "Yellow"
            & $PythonPath -m flask --app app.py db stamp head
            if ($LASTEXITCODE -ne 0) {
                throw "Database migration failed and recovery stamp failed."
            }
            Write-Step "Migration recovery completed (stamped head)." "Yellow"
        }
        else {
            throw "Database migration failed for non-SQLite database. Resolve schema drift or set UKG_ALLOW_ALEMBIC_STAMP_FALLBACK=true to force stamp."
        }
    }
}

if (-not (Test-Path -LiteralPath $PidDir)) {
    New-Item -ItemType Directory -Path $PidDir | Out-Null
}

# Local defaults for HTTP development
$env:FLASK_ENV = "development"
$env:PORT = "$BackendPort"
# runtime_precheck.py reads FRONTEND_PORT when set.
$env:FRONTEND_PORT = "$FrontendPort"
# Honor explicit USE_REDIS from .env when present, otherwise keep local default off.
if (-not $env:USE_REDIS) {
    if ($envMap["USE_REDIS"]) {
        $env:USE_REDIS = $envMap["USE_REDIS"]
    }
    else {
        $env:USE_REDIS = "false"
    }
}
$env:SESSION_COOKIE_SECURE = "false"

Write-Step "Starting backend on http://127.0.0.1:$BackendPort ..."
$backendProcess = Start-Process -FilePath $PythonPath -ArgumentList "app.py" -WorkingDirectory $RepoRoot -PassThru

if (-not (Wait-HttpEndpoint -Url "http://127.0.0.1:$BackendPort/health")) {
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    throw "Backend did not become healthy at /health within timeout."
}
Write-Step "Backend is healthy." "Green"

$frontendProcess = $null
if (-not $NoFrontend) {
    Assert-Path (Join-Path $FrontendDir "node_modules") "Frontend dependencies missing. Run: cd frontend; npm install"
    Write-Step "Starting frontend on http://127.0.0.1:$FrontendPort ..."
    $frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npm run dev -- --hostname 127.0.0.1 --port $FrontendPort" -WorkingDirectory $FrontendDir -PassThru

    $frontendReady = $false
    for ($i = 1; $i -le 180; $i++) {
        if ($frontendProcess.HasExited) {
            break
        }
        if (Test-PortOpen -Port $FrontendPort) {
            $frontendReady = $true
            break
        }
        Start-Sleep -Seconds 1
    }

    if (-not $frontendReady) {
        Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
        $exitCode = $frontendProcess.ExitCode
        throw "Frontend did not respond on port $FrontendPort within timeout. ExitCode=$exitCode"
    }
    Write-Step "Frontend port $FrontendPort is open." "Green"

    if (-not $SkipRouteSmoke) {
        $routeSmokeScript = Join-Path $PSScriptRoot "test_frontend_route_policy.ps1"
        Assert-Path $routeSmokeScript "Route smoke script missing at $routeSmokeScript."
        try {
            & $routeSmokeScript -FrontendPort $FrontendPort
        }
        catch {
            Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
            Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
            throw "Frontend route policy smoke checks failed."
        }
    }
    else {
        Write-Step "Skipping frontend route policy smoke checks (--SkipRouteSmoke)." "Yellow"
    }
}

$pidRecord = @{
    started_at = (Get-Date).ToString("o")
    backend_pid = $backendProcess.Id
    frontend_pid = if ($frontendProcess) { $frontendProcess.Id } else { $null }
}
$pidRecord | ConvertTo-Json | Set-Content -LiteralPath $PidFile -Encoding UTF8

Write-Step "Stack started successfully." "Green"
Write-Host "Backend:  http://127.0.0.1:$BackendPort"
if ($frontendProcess) {
    Write-Host "Frontend: http://127.0.0.1:$FrontendPort"
}
Write-Host "PID file: $PidFile"
Write-Host "Stop command: .\\scripts\\windows\\stop_local_stack.ps1"
