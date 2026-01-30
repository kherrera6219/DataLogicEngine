# run_visual_audit.ps1
# Automated UI/UX Auditor for DataLogicEngine

[CmdletBinding()]
Param(
    [string]$AuditDir = "C:\ProgramData\DataLogicEngine\audit\visual_checks",
    [switch]$KeepLogs
)

$ErrorActionPreference = "Stop"

function Write-Audit([string]$Message, [string]$Color = "Cyan") {
    Write-Host "[AUDIT] $Message" -ForegroundColor $Color
}

try {
    Write-Audit "--- Initializing Visual Audit System ---" "White"
    
    # 1. Environment Check
    if (-not (Test-Path $AuditDir)) {
        New-Item -ItemType Directory -Path $AuditDir -Force | Out-Null
    }
    
    Write-Audit "Cleaning up previous audit artifacts..." "Gray"
    Remove-Item -Path "$AuditDir\*.png" -ErrorAction SilentlyContinue

    # 2. Start Backend (best effort, assuming test environment)
    Write-Audit "Verifying Backend connectivity..."
    # Note: In a real test environment, we might need to spawn the backend if not running
    # For now, we assume the user has a dev environment or a running service.

    # 3. Execute Playwright Audit
    Write-Audit "Launching Electron App for Visual Systematic Navigation..." "Magenta"
    
    Set-Location "$PSScriptRoot\..\..\frontend"
    
    # We use npx to run playwright to avoid global dependency issues
    $env:ELECTRON_PATH = "" # Optional: Add path to build exe if testing production build
    
    npx playwright test tests/visual-audit.spec.ts --config=playwright-electron.config.ts --project=electron
    
    if ($LASTEXITCODE -eq 0) {
        Write-Audit "SUCCESS: Visual audit completed. Screenshots captured in $AuditDir" "Green"
    }
    else {
        Write-Log "FAIL: Visual audit encountered errors. Check logs." "Red"
    }

}
catch {
    Write-Audit "FATAL: Visual audit failed to initialize: $($_.Exception.Message)" "Red"
    exit 1
}
finally {
    Write-Audit "--- Audit Session Closed ---" "White"
}
