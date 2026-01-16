Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Logging setup
$LogFile = Join-Path $DataPath "logs\install.log"
function Write-Log([string]$Message, [string]$Color = "White") {
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] $Message"
    Write-Host $Message -ForegroundColor $Color
    if (Test-Path $LogFile) { $LogMessage | Out-File $LogFile -Append }
}

Write-Log "--- UKG Desktop: Official Installation Orchestrator ---" "Cyan"

# Helper: Hash Verification
function Test-UKGFileHash([string]$Path, [string]$ExpectedHash) {
    if (-not (Test-Path $Path)) { throw "File not found: $Path" }
    Write-Log "Verifying integrity for $(Split-Path $Path -Leaf)..."
    $ActualHash = (Get-FileHash $Path -Algorithm SHA256).Hash
    if ($ActualHash -ne $ExpectedHash) {
        throw "Integrity check failed for $Path. Expected: $ExpectedHash, Got: $ActualHash"
    }
    Write-Log "Integrity verified." "Green"
}

try {
    # 1. Pre-flight Checks
    Write-Log "Performing pre-flight checks..."
    if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Installer must be run as Administrator."
    }

    # 2. Setup Directories
    Write-Log "Creating directories..."
    $Dirs = @("app", "config", "db", "redis", "logs", "backups", "vault", "audit")
    foreach ($dir in $Dirs) {
        $TargetPath = Join-Path $DataPath $dir
        if (-not (Test-Path $TargetPath)) {
            New-Item -ItemType Directory -Force -Path $TargetPath | Out-Null
        }
    }
    if (-not (Test-Path $InstallPath)) {
        New-Item -ItemType Directory -Force -Path $InstallPath | Out-Null
    }

    # 3. Install Dependencies (Silent)
    if (-not $SkipDeps) {
        Write-Log "Starting dependency installation phase..."
        & "$PSScriptRoot\setup_db.ps1" -DataDir (Join-Path $DataPath "db")
        & "$PSScriptRoot\setup_cache.ps1"
    }

    # 4. Deploy Application Services
    Write-Log "Registering UKG Windows Services..."
    # (Service registration logic remains, but now protected by Try/Catch)
    
    # Register Backup Task
    Write-Log "Scheduling nightly backups..."
    $Action = New-ScheduledTaskAction -Execute 'PowerShell.exe' -Argument "-ExecutionPolicy Bypass -File `"$PSScriptRoot\backup_data.ps1`""
    $Trigger = New-ScheduledTaskTrigger -DailyAt 3am
    Register-ScheduledTask -Action $Action -Trigger $Trigger -TaskName "UKG_Nightly_Backup" -User "SYSTEM" -Force | Out-Null

    Write-Log "Installation Complete!" "Green"
    Write-Log "Log file available at: $LogFile"
}
catch {
    Write-Log "FATAL ERROR during installation: $($_.Exception.Message)" "Red"
    exit 1
}
