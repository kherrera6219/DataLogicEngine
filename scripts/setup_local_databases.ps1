# DataLogicEngine Local Database Setup Script for Windows 11
# This script downloads and configures portable database binaries

param(
    [switch]$PostgreSQL,
    [switch]$Redis,
    [switch]$Neo4j,
    [switch]$All,
    [string]$InstallPath = ".\databases"
)

$ErrorActionPreference = "Stop"

# Configuration
$POSTGRES_VERSION = "16.2"
$REDIS_VERSION = "7.2.4"
$NEO4J_VERSION = "5.16.0"

# Download URLs
$POSTGRES_URL = "https://get.enterprisedb.com/postgresql/postgresql-${POSTGRES_VERSION}-1-windows-x64-binaries.zip"
$REDIS_URL = "https://github.com/tporadowski/redis/releases/download/v${REDIS_VERSION}/Redis-x64-${REDIS_VERSION}.zip"
$NEO4J_URL = "https://neo4j.com/artifact.php?name=neo4j-community-${NEO4J_VERSION}-windows.zip"

function Write-Header {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan
}

function Test-CommandExists {
    param([string]$Command)
    $oldPreference = $ErrorActionPreference
    $ErrorActionPreference = 'stop'
    try {
        if (Get-Command $Command) { return $true }
    }
    catch { return $false }
    finally { $ErrorActionPreference = $oldPreference }
}

function Install-PostgreSQL {
    Write-Header "Installing PostgreSQL $POSTGRES_VERSION"
    
    $pgDir = Join-Path $InstallPath "postgresql"
    $pgZip = Join-Path $env:TEMP "postgresql.zip"
    
    if (Test-Path (Join-Path $pgDir "bin\postgres.exe")) {
        Write-Host "PostgreSQL already installed at $pgDir" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Downloading PostgreSQL..." -ForegroundColor Green
    try {
        Invoke-WebRequest -Uri $POSTGRES_URL -OutFile $pgZip -UseBasicParsing
    }
    catch {
        Write-Host "Failed to download PostgreSQL. Please download manually from:" -ForegroundColor Red
        Write-Host $POSTGRES_URL -ForegroundColor Yellow
        return
    }
    
    Write-Host "Extracting PostgreSQL..." -ForegroundColor Green
    New-Item -ItemType Directory -Force -Path $pgDir | Out-Null
    Expand-Archive -Path $pgZip -DestinationPath $env:TEMP -Force
    
    # Move from nested folder
    $extractedDir = Get-ChildItem -Path $env:TEMP -Directory | Where-Object { $_.Name -like "pgsql*" } | Select-Object -First 1
    if ($extractedDir) {
        Move-Item -Path "$($extractedDir.FullName)\*" -Destination $pgDir -Force
    }
    
    Remove-Item $pgZip -Force
    
    # Create data directory
    $pgData = Join-Path $pgDir "data"
    New-Item -ItemType Directory -Force -Path $pgData | Out-Null
    
    Write-Host "PostgreSQL installed successfully!" -ForegroundColor Green
    Write-Host "  Binary path: $pgDir\bin" -ForegroundColor Gray
    Write-Host "  Data path: $pgData" -ForegroundColor Gray
}

function Install-Redis {
    Write-Header "Installing Redis $REDIS_VERSION"
    
    $redisDir = Join-Path $InstallPath "redis"
    $redisZip = Join-Path $env:TEMP "redis.zip"
    
    if (Test-Path (Join-Path $redisDir "redis-server.exe")) {
        Write-Host "Redis already installed at $redisDir" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Downloading Redis for Windows..." -ForegroundColor Green
    try {
        Invoke-WebRequest -Uri $REDIS_URL -OutFile $redisZip -UseBasicParsing
    }
    catch {
        Write-Host "Failed to download Redis. Please download manually from:" -ForegroundColor Red
        Write-Host $REDIS_URL -ForegroundColor Yellow
        return
    }
    
    Write-Host "Extracting Redis..." -ForegroundColor Green
    New-Item -ItemType Directory -Force -Path $redisDir | Out-Null
    Expand-Archive -Path $redisZip -DestinationPath $redisDir -Force
    
    # Move files from nested folder if needed
    $nestedDir = Get-ChildItem -Path $redisDir -Directory | Select-Object -First 1
    if ($nestedDir -and (Test-Path "$($nestedDir.FullName)\redis-server.exe")) {
        Get-ChildItem -Path $nestedDir.FullName | Move-Item -Destination $redisDir -Force
        Remove-Item $nestedDir.FullName -Force -Recurse
    }
    
    Remove-Item $redisZip -Force
    
    # Create data directory
    $redisData = Join-Path $redisDir "data"
    New-Item -ItemType Directory -Force -Path $redisData | Out-Null
    
    Write-Host "Redis installed successfully!" -ForegroundColor Green
    Write-Host "  Path: $redisDir" -ForegroundColor Gray
}

function Install-Neo4j {
    Write-Header "Installing Neo4j Community $NEO4J_VERSION"
    
    $neo4jDir = Join-Path $InstallPath "neo4j"
    $neo4jZip = Join-Path $env:TEMP "neo4j.zip"
    
    if (Test-Path (Join-Path $neo4jDir "bin\neo4j.bat")) {
        Write-Host "Neo4j already installed at $neo4jDir" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Downloading Neo4j Community Edition..." -ForegroundColor Green
    Write-Host "Note: You may need to download manually from neo4j.com if automatic download fails" -ForegroundColor Yellow
    
    try {
        # Neo4j requires accepting license, so direct download may not work
        # Try alternative community mirror
        $altUrl = "https://dist.neo4j.org/neo4j-community-${NEO4J_VERSION}-windows.zip"
        Invoke-WebRequest -Uri $altUrl -OutFile $neo4jZip -UseBasicParsing
    }
    catch {
        Write-Host "Automatic download failed. Please download Neo4j manually:" -ForegroundColor Red
        Write-Host "1. Visit: https://neo4j.com/download-center/#community" -ForegroundColor Yellow
        Write-Host "2. Download Neo4j Community Edition for Windows" -ForegroundColor Yellow
        Write-Host "3. Extract to: $neo4jDir" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Extracting Neo4j..." -ForegroundColor Green
    New-Item -ItemType Directory -Force -Path $neo4jDir | Out-Null
    Expand-Archive -Path $neo4jZip -DestinationPath $env:TEMP -Force
    
    # Move from nested folder
    $extractedDir = Get-ChildItem -Path $env:TEMP -Directory | Where-Object { $_.Name -like "neo4j-community*" } | Select-Object -First 1
    if ($extractedDir) {
        Move-Item -Path "$($extractedDir.FullName)\*" -Destination $neo4jDir -Force
    }
    
    Remove-Item $neo4jZip -Force
    
    Write-Host "Neo4j installed successfully!" -ForegroundColor Green
    Write-Host "  Path: $neo4jDir" -ForegroundColor Gray
    Write-Host "  Default password: neo4j (change on first login)" -ForegroundColor Yellow
}

function Create-DirectoryStructure {
    Write-Header "Creating Directory Structure"
    
    $dirs = @(
        $InstallPath,
        (Join-Path $InstallPath "chroma"),
        (Join-Path $InstallPath "objects")
    )
    
    foreach ($dir in $dirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Force -Path $dir | Out-Null
            Write-Host "Created: $dir" -ForegroundColor Gray
        }
    }
}

function Write-EnvExample {
    $envFile = Join-Path (Split-Path $InstallPath -Parent) ".env.local.example"
    
    $content = @"
# DataLogicEngine Local Database Configuration
# Copy this file to .env.local and customize as needed

# Database Mode: local, cloud, hybrid, auto
DB_MODE=local

# PostgreSQL (Local)
POSTGRES_HOST=127.0.0.1
POSTGRES_LOCAL_PORT=54320
POSTGRES_DB=datalogic
POSTGRES_USER=postgres
POSTGRES_PASSWORD=

# PostgreSQL (Cloud - uncomment to use)
# POSTGRES_CLOUD_URL=postgresql://user:pass@host:5432/db

# Redis (Local)  
REDIS_HOST=127.0.0.1
REDIS_LOCAL_PORT=63790

# Redis (Cloud - uncomment to use)
# REDIS_CLOUD_URL=redis://user:pass@host:6379

# Neo4j (Local)
NEO4J_HOST=127.0.0.1
NEO4J_LOCAL_PORT=7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Neo4j Cloud (Aura - uncomment to use)
# NEO4J_CLOUD_URL=neo4j+s://xxxx.databases.neo4j.io
# NEO4J_CLOUD_USER=neo4j
# NEO4J_CLOUD_PASSWORD=your-password

# Vector Database (ChromaDB local by default)
VECTOR_LOCAL_PATH=./databases/chroma

# Vector Cloud (Pinecone - uncomment to use)
# VECTOR_PROVIDER=pinecone
# VECTOR_API_KEY=your-pinecone-api-key
# VECTOR_ENVIRONMENT=us-east-1

# Object Storage (Local filesystem by default)
OBJECT_LOCAL_PATH=./databases/objects

# Object Storage Cloud (S3/MinIO - uncomment to use)
# OBJECT_ENDPOINT_URL=https://s3.amazonaws.com
# OBJECT_ACCESS_KEY=your-access-key
# OBJECT_SECRET_KEY=your-secret-key
# OBJECT_BUCKET=datalogic
# OBJECT_REGION=us-east-1
"@
    
    Set-Content -Path $envFile -Value $content
    Write-Host "Created environment template: $envFile" -ForegroundColor Green
}

# Main execution
Write-Host @"

╔══════════════════════════════════════════════════════════════╗
║           DataLogicEngine Database Setup Script              ║
║                    Windows 11 Edition                        ║
╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

# Determine what to install
$installPg = $PostgreSQL -or $All
$installRedis = $Redis -or $All
$installNeo4j = $Neo4j -or $All

if (-not ($installPg -or $installRedis -or $installNeo4j)) {
    Write-Host "Usage: .\setup_local_databases.ps1 [-PostgreSQL] [-Redis] [-Neo4j] [-All]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  -PostgreSQL   Install PostgreSQL portable" -ForegroundColor Gray
    Write-Host "  -Redis        Install Redis for Windows" -ForegroundColor Gray
    Write-Host "  -Neo4j        Install Neo4j Community Edition" -ForegroundColor Gray
    Write-Host "  -All          Install all databases" -ForegroundColor Gray
    Write-Host "  -InstallPath  Custom installation path (default: .\databases)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Example: .\setup_local_databases.ps1 -All" -ForegroundColor Green
    exit 0
}

# Create base structure
Create-DirectoryStructure

# Install requested databases
if ($installPg) { Install-PostgreSQL }
if ($installRedis) { Install-Redis }
if ($installNeo4j) { Install-Neo4j }

# Write environment example
Write-EnvExample

Write-Header "Setup Complete!"
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Copy .env.local.example to .env.local" -ForegroundColor Gray
Write-Host "2. Configure your database credentials" -ForegroundColor Gray
Write-Host "3. Start the application - databases will auto-start" -ForegroundColor Gray
Write-Host ""
Write-Host "To manually start databases, use DatabaseLifecycleManager in Python:" -ForegroundColor Yellow
Write-Host '  from backend.storage import get_db_manager' -ForegroundColor Gray
Write-Host '  get_db_manager().start_all()' -ForegroundColor Gray
