Param(
    [switch]$VisualAudit
)

$ErrorActionPreference = "Continue"

Write-Host "--- DataLogicEngine Installer Diagnostics ---" -ForegroundColor Cyan

# 1. Admin Check
$IsAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($IsAdmin) {
    Write-Host "[PASS] Running with Administrative privileges." -ForegroundColor Green
}
else {
    Write-Host "[FAIL] Not running as Administrator. Installer will fail." -ForegroundColor Red
}

# 2. System Integrity & Write Access
Write-Host "`nChecking system integrity & write permissions..." -ForegroundColor Cyan
$TestPaths = @($env:ProgramFiles, $env:ProgramData)
foreach ($path in $TestPaths) {
    if (Test-Path $path) {
        $TestFile = Join-Path $path "ukg_test_$(Get-Random).tmp"
        try {
            New-Item -ItemType File -Path $TestFile -ErrorAction Stop | Out-Null
            Remove-Item -Path $TestFile -ErrorAction Stop
            Write-Host "[PASS] Write access confirmed for $path" -ForegroundColor Green
        }
        catch {
            Write-Host "[FAIL] No write access to $path. Enterprise deployment will fail." -ForegroundColor Red
        }
    }
}

# 3. Source Assets Check (Simulating what electron-builder would provide)
Write-Host "`nChecking source assets..." -ForegroundColor Cyan
$FrontendDist = "c:\software\DataLogicEngine\frontend\dist\win-unpacked"
$BackendDist = "c:\software\DataLogicEngine\dist\DataLogic_Backend"

if (Test-Path $FrontendDist) {
    Write-Host "[PASS] Frontend distribution found at $FrontendDist" -ForegroundColor Green
}
else {
    Write-Host "[WARN] Frontend distribution not found. Run 'npm run electron:dist' first." -ForegroundColor Yellow
}

if (Test-Path $BackendDist) {
    Write-Host "[PASS] Backend distribution found at $BackendDist" -ForegroundColor Green
}
else {
    Write-Host "[WARN] Backend distribution not found. Run pyinstaller build first." -ForegroundColor Yellow
}

# 4. Running DRY RUN Installation
Write-Host "`n--- Executing Dry Run (Simulation) ---" -ForegroundColor Cyan
$InstallScript = Join-Path $PSScriptRoot "install.ps1"

if (Test-Path $InstallScript) {
    powershell.exe -ExecutionPolicy Bypass -File $InstallScript -DryRun
}
else {
    Write-Host "[FATAL] install.ps1 not found in script directory!" -ForegroundColor Red
}

Write-Host "`nDiagnostics Complete." -ForegroundColor Cyan
Write-Host "If the checks above show [PASS] and the Dry Run has no FATAL ERROR, the installer is enterprise-ready."

# Optional Visual Audit
if ($VisualAudit) {
    Write-Host "`n--- Triggering Automated Visual Audit & UI Verification ---" -ForegroundColor Magenta
    $AuditScript = Join-Path $PSScriptRoot "run_visual_audit.ps1"
    if (Test-Path $AuditScript) {
        powershell.exe -ExecutionPolicy Bypass -File $AuditScript
    }
    else {
        Write-Host "[ERROR] run_visual_audit.ps1 not found!" -ForegroundColor Red
    }
}
