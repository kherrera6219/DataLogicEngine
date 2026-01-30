# test_installer.ps1
# Diagnostic script for DataLogicEngine Installer

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

# 2. Source Assets Check (Simulating what electron-builder would provide)
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

# 3. Running DRY RUN Installation
Write-Host "`n--- Executing Dry Run (Simulation) ---" -ForegroundColor Cyan
$InstallScript = Join-Path $PSScriptRoot "install.ps1"

if (Test-Path $InstallScript) {
    powershell.exe -ExecutionPolicy Bypass -File $InstallScript -DryRun
}
else {
    Write-Host "[FATAL] install.ps1 not found in script directory!" -ForegroundColor Red
}

Write-Host "`nDiagnostics Complete." -ForegroundColor Cyan
Write-Host "If the Dry Run above finished without 'FATAL ERROR', the installer is ready."
