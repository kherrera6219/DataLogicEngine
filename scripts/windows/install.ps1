[CmdletBinding()]
Param(
    [switch]$DryRun,
    [bool]$SkipDeps = $true,
    [switch]$Quiet
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Configuration Defaults (Blueprint Aligned)
$InstallPath = $env:ProgramFiles + "\DataLogicEngine"
$DataPath = $env:ProgramData + "\DataLogicEngine"

# Logging setup
$LocalLogDir = Join-Path $PSScriptRoot "logs"
$GlobalLogFile = Join-Path $DataPath "logs\install.log"
$LocalLogFile = Join-Path $LocalLogDir "install.log"

function Write-Log([string]$Message, [string]$Color = "White") {
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $Prefix = if ($DryRun) { "[DRY RUN] " } else { "" }
    $LogMessage = "[$Timestamp] $Prefix$Message"
    
    Write-Host "$Prefix$Message" -ForegroundColor $Color
    
    # Try to log to ProgramData first
    $GlobalLogDir = Split-Path $GlobalLogFile -Parent
    if (Test-Path $GlobalLogDir) {
        $LogMessage | Out-File $GlobalLogFile -Append -ErrorAction SilentlyContinue
    }
    else {
        if (-not (Test-Path $LocalLogDir)) { New-Item -ItemType Directory -Path $LocalLogDir -Force | Out-Null }
        $LogMessage | Out-File $LocalLogFile -Append -ErrorAction SilentlyContinue
    }
}

Write-Log "--- UKG Desktop: Official Installation Orchestrator ---" "Cyan"

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
            if ($DryRun) { Write-Log "DRY RUN: Would create directory $TargetPath" "Gray" }
            else { New-Item -ItemType Directory -Force -Path $TargetPath | Out-Null }
        }
    }
    if (-not (Test-Path $InstallPath)) {
        if ($DryRun) { Write-Log "DRY RUN: Would create directory $InstallPath" "Gray" }
        else { New-Item -ItemType Directory -Force -Path $InstallPath | Out-Null }
    }

    # 3. Registry Registration
    Write-Log "Registering application in Windows Registry..."
    $RegPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\DataLogicEngine"
    if ($DryRun) {
        Write-Log "DRY RUN: Would create registry key $RegPath" "Gray"
    }
    else {
        if (-not (Test-Path $RegPath)) { New-Item -Path $RegPath -Force | Out-Null }
        Set-ItemProperty -Path $RegPath -Name "DisplayName" -Value "DataLogicEngine Desktop"
        Set-ItemProperty -Path $RegPath -Name "DisplayVersion" -Value "0.1.0"
        Set-ItemProperty -Path $RegPath -Name "Publisher" -Value "UKG"
        Set-ItemProperty -Path $RegPath -Name "InstallLocation" -Value $InstallPath
        Set-ItemProperty -Path $RegPath -Name "UninstallString" -Value "powershell.exe -ExecutionPolicy Bypass -File `"$PSScriptRoot\uninstall.ps1`""
        Set-ItemProperty -Path $RegPath -Name "DisplayIcon" -Value (Join-Path $InstallPath "app\DataLogicEngine.exe")
    }

    # 4. Success Completion
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
    
    if (-not $Quiet) {
        Write-Host "`nPress any key to close this window..." -ForegroundColor Cyan
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
    exit 1
}
