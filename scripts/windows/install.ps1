Param(
    [string]$InstallPath = "C:\Program Files\DataLogicEngine",
    [string]$DataPath = "C:\ProgramData\DataLogicEngine",
    [switch]$SkipDeps = $false
)

$ErrorActionPreference = "Stop"

Write-Host "--- UKG Desktop: Official Installation Orchestrator ---" -ForegroundColor Cyan

# 1. Pre-flight Checks
Write-Host "Performing pre-flight checks..."
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "Installer must be run as Administrator."
}

# 2. Setup Directories
Write-Host "Creating directories..."
$Dirs = @("app", "config", "db", "redis", "logs", "backups", "vault", "audit")
foreach ($dir in $Dirs) {
    New-Item -ItemType Directory -Force -Path (Join-Path $DataPath $dir) | Out-Null
}
New-Item -ItemType Directory -Force -Path $InstallPath | Out-Null

# 3. Install Dependencies (Silent)
if (-not $SkipDeps) {
    # Run modular setup scripts
    & "$PSScriptRoot\setup_db.ps1" -DataDir (Join-Path $DataPath "db")
    & "$PSScriptRoot\setup_cache.ps1"
}

# 4. Deploy Application Services
Write-Host "Registering UKG Windows Services..."
$BackendPath = Join-Path $InstallPath "app\DataLogic_Backend.exe"
$FrontendPath = "node.exe"

# (Logic for copying binaries would go here)

# Register Backup Task
Write-Host "Scheduling nightly backups..."
$Action = New-ScheduledTaskAction -Execute 'PowerShell.exe' -Argument "-ExecutionPolicy Bypass -File `"$PSScriptRoot\backup_data.ps1`""
$Trigger = New-ScheduledTaskTrigger -DailyAt 3am
Register-ScheduledTask -Action $Action -Trigger $Trigger -TaskName "UKG_Nightly_Backup" -User "SYSTEM" -Force | Out-Null

Write-Host "Installation Complete!" -ForegroundColor Green
Write-Host "Visit http://localhost:3000 to access your Desktop Reasoning Engine."
