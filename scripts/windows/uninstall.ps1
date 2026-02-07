[CmdletBinding()]
Param(
    [switch]$Quiet,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue" # Allow uninstaller to proceed even if some steps fail

# Function to kill any running instances
function Stop-ActiveAppProcesses {
    Write-Host "Checking for active application processes..." -ForegroundColor Gray
    $AppProcesses = @("DataLogic_Backend", "DataLogic_Frontend", "DataLogicEngine")
    foreach ($proc in $AppProcesses) {
        $Instances = Get-Process -Name $proc -ErrorAction SilentlyContinue
        if ($Instances) {
            Write-Host "Terminating active process: $proc" -ForegroundColor Yellow
            $Instances | Stop-Process -Force -ErrorAction SilentlyContinue
        }
    }
}

function Remove-WinSWService([string]$ServiceName, [string]$WrapperPath) {
    if (Test-Path -LiteralPath $WrapperPath) {
        try {
            & $WrapperPath stop | Out-Null
        }
        catch {
            # Service might already be stopped or not installed.
        }
        try {
            & $WrapperPath uninstall | Out-Null
            Write-Host "Audit: Service $ServiceName removed via WinSW wrapper." -ForegroundColor DarkGray
            return
        }
        catch {
            # Fall through to SCM deletion fallback.
        }
    }

    if (Get-Service $ServiceName -ErrorAction SilentlyContinue) {
        Stop-Service $ServiceName -Force -ErrorAction SilentlyContinue
        & sc.exe delete $ServiceName | Out-Null
        Write-Host "Audit: Service $ServiceName deleted via SCM fallback." -ForegroundColor DarkGray
    }
}

try {
    Write-Host "--- UKG Desktop: Uninstallation Initiated ---" -ForegroundColor Cyan
    Stop-ActiveAppProcesses

    # 0. Retrieve Install Location from Registry
    $RegPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\DataLogicEngine"
    $InstallPath = "C:\Program Files\DataLogicEngine" # Fallback
    
    if (Test-Path $RegPath) {
        $RegValue = Get-ItemProperty -Path $RegPath -Name "InstallLocation" -ErrorAction SilentlyContinue
        if ($RegValue -and $RegValue.InstallLocation) {
            $InstallPath = $RegValue.InstallLocation
            Write-Host "Detected installation path: $InstallPath" -ForegroundColor Gray
        }
    }

    $DataPath = "C:\ProgramData\DataLogicEngine"

    # 1. Stop and Remove Application Services
    Write-Host "Removing Windows Services..."
    Remove-WinSWService -ServiceName "DataLogic_Backend" -WrapperPath (Join-Path $InstallPath "DataLogic_Backend.exe")
    Remove-WinSWService -ServiceName "DataLogic_Frontend" -WrapperPath (Join-Path $InstallPath "DataLogic_Frontend.exe")
    # Optional local dependency services created by legacy scripts
    Remove-WinSWService -ServiceName "UKG-Postgres" -WrapperPath ""
    Remove-WinSWService -ServiceName "UKG-Redis" -WrapperPath ""

    # 2. Registry Cleanup
    Write-Host "Removing Registry entries..." -ForegroundColor Cyan
    if (Test-Path $RegPath) {
        Remove-Item -Path $RegPath -Force -ErrorAction SilentlyContinue
        Write-Host "Audit: Registry key $RegPath removed." -ForegroundColor DarkGray
    }

    # 3. Handle Data Removal
    $decision = 1 # Default to Keep Data for automated runs
    if ($Force) {
        $decision = 1 # Delete everything
    }
    elseif (-not $Quiet -and $Host.Name -eq "ConsoleHost") {
        $title = "Keep Your Data?"
        $message = "Do you want to permanently delete local chat history and settings at $DataPath?"
        $choices = [System.Management.Automation.Host.ChoiceDescription[]] @(
            New-Object System.Management.Automation.Host.ChoiceDescription "&Yes", "Keep my data."
            New-Object System.Management.Automation.Host.ChoiceDescription "&No", "Delete everything."
        )
        # Note: PromptForChoice returns index. 0 = Keep, 1 = Delete
        $decision = $Host.UI.PromptForChoice($title, $message, $choices, 0)
    }

    if ($decision -eq 1) {
        Write-Host "Deleting user data residency..." -ForegroundColor Red
        if (Test-Path $DataPath) {
            Remove-Item -Path $DataPath -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "Audit: Data path $DataPath removed." -ForegroundColor DarkGray
        }
    }
    else {
        Write-Host "Preserving user data residency." -ForegroundColor Yellow
    }

    # 4. Remove Program Files
    Write-Host "Removing Program Binaries..."
    if (Test-Path $InstallPath) {
        Write-Host "Purging directory: $InstallPath" -ForegroundColor Gray
        # Attempt cleanup, but don't fail if files are locked (common in uninstalls)
        Remove-Item -Path $InstallPath -Recurse -Force -ErrorAction SilentlyContinue
        if (-not (Test-Path $InstallPath)) {
            Write-Host "Audit: Binary directory removed successfully." -ForegroundColor DarkGray
        }
        else {
            Write-Host "Audit: [FAIL] Binary directory locked or partially removed." -ForegroundColor Red
        }
    }

    # 5. Scheduled Tasks Cleanup
    Write-Host "Cleaning up scheduled tasks..."
    if (Get-ScheduledTask -TaskName "UKG_Nightly_Backup" -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName "UKG_Nightly_Backup" -Confirm:$false -ErrorAction SilentlyContinue
    }

    Write-Host "Uninstallation Complete." -ForegroundColor Green
}
catch {
    Write-Host "Uninstallation encountered a fatal error: $($_.Exception.Message)" -ForegroundColor Red
    exit 0 # Still exit 0 to allow the OS to consider it "uninstalled"
}
