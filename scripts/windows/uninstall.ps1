Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

try {
    Write-Host "--- UKG Desktop: Uninstallation Initiated ---" -ForegroundColor Cyan

    # 1. Stop and Remove Application Services
    Write-Host "Stopping Services..."
    Stop-Service "DataLogic_Backend" -Force -ErrorAction SilentlyContinue
    Stop-Service "DataLogic_Frontend" -Force -ErrorAction SilentlyContinue
    Stop-Service "UKG-Postgres" -Force -ErrorAction SilentlyContinue
    Stop-Service "UKG-Redis" -Force -ErrorAction SilentlyContinue

    Write-Host "Unregistering Services..."
    & "C:\Program Files\DataLogicEngine\app\DataLogic_Backend.exe" uninstall
    & "C:\Program Files\DataLogicEngine\app\DataLogic_Frontend.exe" uninstall

    # 2. Ask whether to keep data
    $title = "Keep Your Data?"
    $message = "Do you want to keep your local chat history, profiles, and settings? (Saved in C:\ProgramData\DataLogicEngine)"
    $choices = [System.Management.Automation.Host.ChoiceDescription[]] @(
        New-Object System.Management.Automation.Host.ChoiceDescription "&Yes", "Keep my data for future installs."
        New-Object System.Management.Automation.Host.ChoiceDescription "&No", "Permanently delete everything."
    )

    $decision = $Host.UI.PromptForChoice($title, $message, $choices, 0)

    if ($decision -eq 1) {
        Write-Host "Permanently deleting user data..." -ForegroundColor Red
        Remove-Item -Path "C:\ProgramData\DataLogicEngine" -Recurse -Force
    }
    else {
        Write-Host "Preserving user data residency." -ForegroundColor Yellow
    }

    # 3. Remove Program Files
    Write-Host "Removing Program Binaries..."
    Remove-Item -Path "C:\Program Files\DataLogicEngine" -Recurse -Force

    Write-Host "Uninstallation Complete." -ForegroundColor Green
}
catch {
    Write-Host "Uninstallation encountered errors: $($_.Exception.Message)" -ForegroundColor Yellow
    # Still attempt to return success as partial uninstall is better than none
    exit 0
}
