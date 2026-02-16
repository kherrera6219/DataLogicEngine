[CmdletBinding()]
Param(
    [switch]$DryRun,
    [bool]$SkipDeps = $true,
    [switch]$Quiet,
    [switch]$Silent,
    [string]$InstallPath = (Join-Path $env:ProgramFiles "DataLogicEngine"),
    [string]$DataPath = (Join-Path $env:ProgramData "DataLogicEngine")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($Silent) {
    $Quiet = $true
}

# Logging setup
$LocalLogDir = Join-Path $PSScriptRoot "logs"
$GlobalLogFile = Join-Path $DataPath "logs\install.log"
$LocalLogFile = Join-Path $LocalLogDir "install.log"

function Write-Log([string]$Message, [string]$Color = "White") {
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $Prefix = if ($DryRun) { "[DRY RUN] " } else { "" }
    $LogMessage = "[$Timestamp] $Prefix$Message"
    
    Write-Host "$Prefix$Message" -ForegroundColor $Color
    
    $DidPersist = $false

    # Try to log to ProgramData first
    $GlobalLogDir = Split-Path $GlobalLogFile -Parent
    if (Test-Path $GlobalLogDir) {
        try {
            $LogMessage | Out-File $GlobalLogFile -Append -ErrorAction Stop
            $DidPersist = $true
        }
        catch {
            # Fall back to local script folder log below.
        }
    }

    if (-not $DidPersist) {
        try {
            if (-not (Test-Path $LocalLogDir)) { New-Item -ItemType Directory -Path $LocalLogDir -Force | Out-Null }
            $LogMessage | Out-File $LocalLogFile -Append -ErrorAction Stop
        }
        catch {
            # Logging should never block installer control flow.
        }
    }
}

function Protect-DirectoryAcl([string]$TargetPath) {
    if ($DryRun) {
        Write-Log "DRY RUN: Would apply restricted ACLs to $TargetPath" "Gray"
        return
    }

    if (-not (Test-Path -LiteralPath $TargetPath)) {
        return
    }

    try {
        & icacls $TargetPath /inheritance:r /grant:r "SYSTEM:(OI)(CI)(F)" "Administrators:(OI)(CI)(F)" | Out-Null
        Write-Log "[PASS] Restricted ACLs applied to $TargetPath" "Green"
    }
    catch {
        Write-Log "[WARN] Failed to apply restricted ACLs on ${TargetPath}: $($_.Exception.Message)" "Yellow"
    }
}

# Shared integrity helper for dependency installers and diagnostics.
function Test-UKGFileHash {
    [CmdletBinding()]
    Param(
        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [ValidateNotNullOrEmpty()]
        [string]$ExpectedHash
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Hash verification failed. File not found: $Path"
    }

    $NormalizedExpected = ($ExpectedHash -replace '\s', '').ToUpperInvariant()
    if ($NormalizedExpected -notmatch '^[A-F0-9]{64}$') {
        throw "Hash verification failed. Expected SHA-256 hash must be a 64-character hex string."
    }

    $ActualHash = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($ActualHash -ne $NormalizedExpected) {
        throw "Hash mismatch for $Path. Expected $NormalizedExpected but got $ActualHash."
    }

    Write-Log "[PASS] Hash verification passed for $Path" "Green"
    return $true
}

# Function to get hardware telemetry
function Get-SystemSnapshot {
    $Mem = Get-CimInstance Win32_OperatingSystem | Select-Object TotalVisibleMemorySize, FreePhysicalMemory
    $Disk = Get-PSDrive C | Select-Object Used, Free
    Write-Log "--- System Telemetry Snapshot ---" "Gray"
    Write-Log "OS Architecture: $((Get-CimInstance Win32_Processor).AddressWidth)-bit" "Gray"
    Write-Log "Total Physical RAM: $([Math]::Round($Mem.TotalVisibleMemorySize / 1MB, 2)) GB" "Gray"
    Write-Log "Available C: Drive Space: $([Math]::Round($Disk.Free / 1GB, 2)) GB" "Gray"
}

# Function for pre-flight requirements
function Test-SystemRequirements {
    $DiskFree = (Get-PSDrive C).Free / 1GB
    $MemTotal = (Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize / 1MB
    
    if ($DiskFree -lt 2) { 
        Write-Log "[WARN] Available disk space is low ($([Math]::Round($DiskFree, 2)) GB). 2GB recommended." "Yellow"
    }
    else {
        Write-Log "[PASS] Disk space requirement met." "Green"
    }
    
    if ($MemTotal -lt 4) {
        Write-Log "[WARN] Total RAM is low ($([Math]::Round($MemTotal, 2)) GB). 4GB recommended for enterprise stability." "Yellow"
    }
    else {
        Write-Log "[PASS] RAM requirement met." "Green"
    }
}

# Function to check port availability
function Test-PortAvailability([int]$Port, [string]$ServiceName) {
    if (Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue) {
        Write-Log "[WARN] Port $Port (standard for $ServiceName) is already in use. Local setup might conflict." "Yellow"
    }
    else {
        Write-Log "[PASS] Port $Port available for $ServiceName." "Green"
    }
}

function Install-WinSWService([string]$ServiceName, [string]$WrapperPath) {
    if (-not (Test-Path -LiteralPath $WrapperPath)) {
        Write-Log "[WARN] Service wrapper missing for $ServiceName at $WrapperPath. Skipping service install." "Yellow"
        return
    }

    if ($DryRun) {
        Write-Log "DRY RUN: Would install and start service $ServiceName using $WrapperPath" "Gray"
        return
    }

    try {
        & $WrapperPath install | Out-Null
        Write-Log "[PASS] Service installed: $ServiceName" "Green"
    }
    catch {
        Write-Log "[WARN] Service install failed for ${ServiceName}: $($_.Exception.Message)" "Yellow"
        return
    }

    try {
        & $WrapperPath start | Out-Null
        Write-Log "[PASS] Service started: $ServiceName" "Green"
    }
    catch {
        Write-Log "[WARN] Service start failed for ${ServiceName}: $($_.Exception.Message)" "Yellow"
    }
}

Write-Log "--- UKG Desktop: Official Installation Orchestrator ---" "Cyan"
Get-SystemSnapshot

try {
    # 1. Pre-flight Checks
    Write-Log "Performing pre-flight checks..."
    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        if ($DryRun) {
            Write-Log "[WARN] Dry run is not elevated. Privileged operations are simulated only." "Yellow"
        }
        else {
            throw "Installer must be run as Administrator."
        }
    }
    
    Test-SystemRequirements
    Test-PortAvailability 5432 "PostgreSQL"
    Test-PortAvailability 6379 "Redis"

    # 2. Setup Directories
    Write-Log "Creating directories..."
    $CreatedDirs = @()
    $Dirs = @("app", "config", "db", "redis", "logs", "backups", "vault", "audit")
    foreach ($dir in $Dirs) {
        $TargetPath = Join-Path $DataPath $dir
        if (-not (Test-Path $TargetPath)) {
            if ($DryRun) { Write-Log "DRY RUN: Would create directory $TargetPath" "Gray" }
            else { 
                New-Item -ItemType Directory -Force -Path $TargetPath | Out-Null 
                $CreatedDirs += $TargetPath
            }
        }
    }
    if (-not (Test-Path $InstallPath)) {
        if ($DryRun) { Write-Log "DRY RUN: Would create directory $InstallPath" "Gray" }
        else { 
            New-Item -ItemType Directory -Force -Path $InstallPath | Out-Null 
            $CreatedDirs += $InstallPath
        }
    }

    # 2b. Harden local log and vault storage directories with restricted ACLs.
    Protect-DirectoryAcl -TargetPath (Join-Path $DataPath "logs")
    Protect-DirectoryAcl -TargetPath (Join-Path $DataPath "audit")
    Protect-DirectoryAcl -TargetPath (Join-Path $DataPath "vault")

    # 3. Registry Registration
    Write-Log "Registering application in Windows Registry..."
    $RegPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\DataLogicEngine"
    if ($DryRun) {
        Write-Log "DRY RUN: Would create registry key $RegPath" "Gray"
    }
    else {
        if (-not (Test-Path $RegPath)) { New-Item -Path $RegPath -Force | Out-Null }
        Set-ItemProperty -Path $RegPath -Name "DisplayName" -Value "DataLogicEngine Desktop"
        Set-ItemProperty -Path $RegPath -Name "DisplayVersion" -Value "1.2.4.0"
        Set-ItemProperty -Path $RegPath -Name "Publisher" -Value "UKG"
        Set-ItemProperty -Path $RegPath -Name "InstallLocation" -Value $InstallPath
        Set-ItemProperty -Path $RegPath -Name "UninstallString" -Value "powershell.exe -ExecutionPolicy Bypass -File `"$PSScriptRoot\uninstall.ps1`""
        Set-ItemProperty -Path $RegPath -Name "DisplayIcon" -Value (Join-Path $InstallPath "DataLogic_Backend_App.exe")
    }

    # 4. Install Windows services when WinSW wrappers are available.
    Write-Log "Installing service wrappers..."
    Install-WinSWService -ServiceName "DataLogic_Backend" -WrapperPath (Join-Path $InstallPath "DataLogic_Backend.exe")
    Install-WinSWService -ServiceName "DataLogic_Frontend" -WrapperPath (Join-Path $InstallPath "DataLogic_Frontend.exe")

    # 5. Success Completion
    Write-Log "Installation Process Finished!" "Green"
    
    if (-not $DryRun -and -not $Quiet) {
        Write-Host "`nPress any key to close this window..." -ForegroundColor Cyan
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
}
catch {
    Write-Log "FATAL ERROR during installation: $($_.Exception.Message)" "Red"
    
    if (-not $DryRun) {
        Write-Log "Initiating Atomic Rollback..." "Yellow"
        # 1. Remove Registry Key
        if (Test-Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\DataLogicEngine") {
            Remove-Item -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\DataLogicEngine" -Force -ErrorAction SilentlyContinue
        }
        # 2. Log manual cleanup reminder
        Write-Log "Rollback: Registry entries removed. Please manually verify $InstallPath cleanup if needed." "Gray"
    }
    
    if (-not $Quiet -and -not $DryRun) {
        Write-Host "`nPress any key to close this window..." -ForegroundColor Cyan
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
    exit 1
}
