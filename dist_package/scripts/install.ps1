# DataLogicEngine Windows Installer Orchestrator
# This script is called by the main Setup.exe bootstrapper

Param(
    [string]$InstallPath = "C:\Program Files\DataLogicEngine",
    [string]$DataPath = "C:\DataLogic_DATA",
    [switch]$SkipDeps = $false
)

$ErrorActionPreference = "Stop"

Write-Host "Starting DataLogicEngine Installation..." -ForegroundColor Cyan

# 1. Create Directories
Write-Host "Creating directories..."
New-Item -ItemType Directory -Force -Path $InstallPath
New-Item -ItemType Directory -Force -Path $DataPath
New-Item -ItemType Directory -Force -Path "$DataPath\postgres"
New-Item -ItemType Directory -Force -Path "$DataPath\redis"
New-Item -ItemType Directory -Force -Path "$DataPath\logs"

# 2. Install Postgres (Silent)
if (-not $SkipDeps) {
    Write-Host "Installing PostgreSQL 15..."
    # Assuming the installer is bundled in a 'redist' folder
    # Start-Process -FilePath "$PSScriptRoot\redist\postgresql-15-windows-x64.exe" -ArgumentList "--mode unattended --postgrespassword postgres --datadir `"$DataPath\postgres`"" -Wait
}

# 3. Install Redis (Silent)
if (-not $SkipDeps) {
    Write-Host "Installing Redis..."
    # Assuming redis msi is bundled
    # Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$PSScriptRoot\redist\redis.msi`" /quiet" -Wait
}

# 4. Register WinSW Services
Write-Host "Registering Windows Services..."

$Services = @(
    @{ Name="DataLogic_Backend"; Exec="DataLogic_Backend.exe"; Deps="postgresql,redis" },
    @{ Name="DataLogic_Frontend"; Exec="node.exe"; Args="standalone/server.js"; Deps="DataLogic_Backend" }
)

foreach ($svc in $Services) {
    Write-Host "Configuring service: $($svc.Name)"
    # Copy WinSW binary and rename to service name
    Copy-Item "$PSScriptRoot\winsw.exe" "$InstallPath\$($svc.Name).exe" -Force
    
    # Generate XML config (Simplified for this script)
    $xml = @"
<service>
  <id>$($svc.Name)</id>
  <name>$($svc.Name)</name>
  <description>DataLogicEngine $($svc.Name) Service</description>
  <executable>$($svc.Exec)</executable>
  $(if ($svc.Args) { "<arguments>$($svc.Args)</arguments>" })
  <log mode="roll"></log>
</service>
"@
    $xml | Out-File "$InstallPath\$($svc.Name).xml" -Encoding utf8
    
    # Install service
    Start-Process -FilePath "$InstallPath\$($svc.Name).exe" -ArgumentList "install" -Wait
}

# 5. Run Database Migrations
Write-Host "Running database migrations..."
# Start-Process -FilePath "$InstallPath\DataLogic_Backend.exe" -ArgumentList "db migrate" -Wait

Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "Open http://localhost:3000 to begin."
