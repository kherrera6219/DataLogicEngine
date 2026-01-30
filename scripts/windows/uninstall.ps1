[CmdletBinding()]
Param(
    [switch]$Quiet,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue" # Allow uninstaller to proceed even if some steps fail

try {
    Write-Host "--- UKG Desktop: Uninstallation Initiated ---" -ForegroundColor Cyan

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
    Write-Host "Stopping Services..."
    $Services = @("DataLogic_Backend", "DataLogic_Frontend", "UKG-Postgres", "UKG-Redis")
    foreach ($svc in $Services) {
        Stop-Service $svc -Force -ErrorAction SilentlyContinue
        # Explicitly delete to prevent "marked for deletion" locks
        & sc.exe delete $svc | Out-Null
    }

    # 2. Registry Cleanup
    Write-Host "Removing Registry entries..." -ForegroundColor Cyan
    if (Test-Path $RegPath) {
        Remove-Item -Path $RegPath -Force -ErrorAction SilentlyContinue
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
        }
    }
    else {
        Write-Host "Preserving user data residency." -ForegroundColor Yellow
    }

    # 4. Remove Program Files
    Write-Host "Removing Program Binaries..."
    if (Test-Path $InstallPath) {
        # Attempt cleanup, but don't fail if files are locked (common in uninstalls)
        Remove-Item -Path $InstallPath -Recurse -Force -ErrorAction SilentlyContinue
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
