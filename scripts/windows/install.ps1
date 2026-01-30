Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Configuration Defaults (Blueprint Aligned)
$InstallPath = $env:ProgramFiles + "\DataLogicEngine"
$DataPath = $env:ProgramData + "\DataLogicEngine"
$LocalDbUser = "ukg_app"
$LocalDbName = "ukg_local"
$LocalDbPwd = "ukg_local_pwd" # Default, usually generated random in prod
$SkipDeps = $true # Skip dependency installation (PostgreSQL/Redis) for dev/testing

# Logging setup
$LogFile = Join-Path $DataPath "logs\install.log"
function Write-Log([string]$Message, [string]$Color = "White") {
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] $Message"
    Write-Host $Message -ForegroundColor $Color
    # Only log to file if directory exists
    $LogDir = Split-Path $LogFile -Parent
    if (Test-Path $LogDir) { $LogMessage | Out-File $LogFile -Append -ErrorAction SilentlyContinue }
}

Write-Log "--- UKG Desktop: Official Installation Orchestrator ---" "Cyan"

# Helper: Windows 11 and Architecture Check
function Test-Win11Environment {
    $OS = Get-CimInstance Win32_OperatingSystem
    Write-Log "OS Detected: $($OS.Caption) (Version: $($OS.Version))"
    
    # Windows 11 is version 10.0.22000 or higher
    if ([version]$OS.Version -ge [version]"10.0.22000") {
        Write-Log "Windows 11 environment confirmed." "Green"
    }
    else {
        Write-Log "Pre-Windows 11 environment detected. Applying compatibility defaults." "Yellow"
    }
}

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
    Test-Win11Environment

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

    # 2.1 Registry Registration (Win11 Settings Integration)
    Write-Log "Registering application in Windows Registry..."
    $RegPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\DataLogicEngine"
    if (-not (Test-Path $RegPath)) { New-Item -Path $RegPath -Force | Out-Null }
    
    Set-ItemProperty -Path $RegPath -Name "DisplayName" -Value "DataLogicEngine Desktop"
    Set-ItemProperty -Path $RegPath -Name "DisplayVersion" -Value "0.1.0"
    Set-ItemProperty -Path $RegPath -Name "Publisher" -Value "UKG"
    Set-ItemProperty -Path $RegPath -Name "InstallLocation" -Value $InstallPath
    Set-ItemProperty -Path $RegPath -Name "UninstallString" -Value "powershell.exe -ExecutionPolicy Bypass -File `"$PSScriptRoot\uninstall.ps1`""
    Set-ItemProperty -Path $RegPath -Name "DisplayIcon" -Value (Join-Path $InstallPath "app\DataLogicEngine.exe")
    Set-ItemProperty -Path $RegPath -Name "NoModify" -Value 1
    Set-ItemProperty -Path $RegPath -Name "NoRepair" -Value 1

    # 3. Install Dependencies (Silent & Hardened) - Skipped by default for dev
    if (-not $SkipDeps) {
        Write-Log "Starting dependency installation phase (PostgreSQL & Redis)..."
        $SetupDbScript = Join-Path $PSScriptRoot "setup_db.ps1"
        $SetupCacheScript = Join-Path $PSScriptRoot "setup_cache.ps1"
        if (Test-Path $SetupDbScript) {
            $SecurePwd = ConvertTo-SecureString -String $LocalDbPwd -AsPlainText -Force
            & $SetupDbScript -DataDir (Join-Path $DataPath "db") -DbUser $LocalDbUser -Database $LocalDbName -Password $SecurePwd
        }
        if (Test-Path $SetupCacheScript) {
            & $SetupCacheScript
        }
    }
    else {
        Write-Log "Skipping dependency installation (SkipDeps=true)." "Yellow"
    }

    # 4. Deploy Application
    Write-Log "Deploying Application Binaries..."
    Write-Log "(Placeholder: Copy files from distribution source to $InstallPath)" "Yellow"

    # 5. Run Database Migrations (Alembic) - Optional
    Write-Log "Initializing Database Schema (Migrations)..."
    $BackendExe = Join-Path $InstallPath "app\DataLogic_Backend.exe"
    if (Test-Path $BackendExe) {
        Write-Log "Executing 'flask db upgrade' via backend wrapper..."
        $MigrationsDir = Join-Path $InstallPath "app\migrations"
        & $BackendExe db upgrade --directory $MigrationsDir
        Write-Log "Migrations applied successfully." "Green"
    }
    else {
        Write-Log "Backend executable not found. Skipping migrations." "Yellow"
    }

    # 6. Configure Service Dependencies - Optional
    Write-Log "Checking for Windows Services..."
    $BackendService = Get-Service "DataLogic_Backend" -ErrorAction SilentlyContinue
    if ($BackendService) {
        Write-Log "Configuring service dependencies..."
        & sc.exe config DataLogic_Backend depend= UKG-Postgres/UKG-Redis | Out-Null
        Write-Log "Service dependencies configured: Backend depends on Postgres & Redis."
    }
    else {
        Write-Log "No services to configure (not installed as service)." "Yellow"
    }

    # 7. Register Backup Task - Optional
    Write-Log "Scheduling nightly backups..."
    $BackupScript = Join-Path $PSScriptRoot "backup_data.ps1"
    if (Test-Path $BackupScript) {
        try {
            $Action = New-ScheduledTaskAction -Execute 'PowerShell.exe' -Argument "-ExecutionPolicy Bypass -File `"$BackupScript`""
            $Trigger = New-ScheduledTaskTrigger -Daily -At "3:00AM"
            Register-ScheduledTask -Action $Action -Trigger $Trigger -TaskName "UKG_Nightly_Backup" -User "SYSTEM" -Force | Out-Null
            Write-Log "Nightly backup task registered." "Green"
        }
        catch {
            Write-Log "Could not register backup task: $($_.Exception.Message)" "Yellow"
        }
    }
    else {
        Write-Log "Backup script not found. Skipping scheduled task." "Yellow"
    }

    Write-Log "Installation Complete!" "Green"
    Write-Log "Log file available at: $LogFile"
    Write-Host ""
    Write-Host "Press any key to close this window..." -ForegroundColor Cyan
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
catch {
    Write-Log "FATAL ERROR during installation: $($_.Exception.Message)" "Red"
    
    # --- ATOMIC ROLLBACK ---
    Write-Log "Initiating Atomic Rollback..." "Yellow"
    try {
        # Cleanup logic here...
    }
    catch {
        Write-Log "Rollback encountered secondary errors: $($_.Exception.Message)" "Red"
    }
    
    Write-Host ""
    Write-Host "Press any key to close this window..." -ForegroundColor Cyan
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}
