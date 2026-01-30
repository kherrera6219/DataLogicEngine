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
    if (Test-Path "C:\Program Files\DataLogicEngine\app\DataLogic_Backend.exe") {
        & "C:\Program Files\DataLogicEngine\app\DataLogic_Backend.exe" uninstall
    }

    # 2. Registry Cleanup
    Write-Host "Removing Registry entries..." -ForegroundColor Cyan
    $RegPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\DataLogicEngine"
    if (Test-Path $RegPath) {
        Remove-Item -Path $RegPath -Force
    }

    # 3. Ask whether to keep data
    $title = "Keep Your Data?"
    $message = "Do you want to keep your local chat history, profiles, and settings? (Saved in C:\ProgramData\DataLogicEngine)"
    $choices = [System.Management.Automation.Host.ChoiceDescription[]] @(
        New-Object System.Management.Automation.Host.ChoiceDescription "&Yes", "Keep my data for future installs."
        New-Object System.Management.Automation.Host.ChoiceDescription "&No", "Permanently delete everything."
    )

    # Use standard host UI but handle non-interactive environments
    if ($Host.Name -ne "ConsoleHost") {
        Write-Host "Non-interactive environment detected. Defaulting to Preserve Data." -ForegroundColor Yellow
        $decision = 0
    } else {
        $decision = $Host.UI.PromptForChoice($title, $message, $choices, 0)
    }

    if ($decision -eq 1) {
        Write-Host "Permanently deleting user data residency..." -ForegroundColor Red
        if (Test-Path "C:\ProgramData\DataLogicEngine") {
            Remove-Item -Path "C:\ProgramData\DataLogicEngine" -Recurse -Force
        }
    }
    else {
        Write-Host "Preserving user data residency." -ForegroundColor Yellow
    }

    # 4. Remove Program Files
    Write-Host "Removing Program Binaries..."
    if (Test-Path "C:\Program Files\DataLogicEngine") {
        Remove-Item -Path "C:\Program Files\DataLogicEngine" -Recurse -Force
    }

    # 5. Scheduled Tasks Cleanup
    Write-Host "Cleaning up scheduled tasks..."
    if (Get-ScheduledTask -TaskName "UKG_Nightly_Backup" -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName "UKG_Nightly_Backup" -Confirm:$false
    }

    Write-Host "Uninstallation Complete." -ForegroundColor Green
}
catch {
    Write-Host "Uninstallation encountered errors: $($_.Exception.Message)" -ForegroundColor Yellow
    exit 0
}
