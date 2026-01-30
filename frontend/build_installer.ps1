# build_installer.ps1
# This script handles the professional NSIS installer build for DataLogicEngine.
# It requires elevation to extract winCodeSign components properly on Windows.

$ErrorActionPreference = "Stop"

# Check for administrative privileges
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Re-launching as Administrator..." -ForegroundColor Cyan
    Start-Process powershell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

try {
    Write-Host "--- DataLogicEngine Production Build Orchestrator ---" -ForegroundColor Green
    Write-Host "Current Directory: $(Get-Location)"

    # Ensure we are in the frontend directory
    $FrontendDir = "c:\software\DataLogicEngine\frontend"
    if ((Get-Location).Path -ne $FrontendDir) {
        Set-Location $FrontendDir
    }

    # 1. Environment Preparation
    Write-Host "Setting up environment (Bypassing Code Signing)..." -ForegroundColor Yellow
    $env:CSC_SKIP = "true"

    # 2. Re-trigger Next.js Build (Ensure up to date)
    Write-Host "Running Next.js production build..." -ForegroundColor Cyan
    npm run build

    # 3. Compiling Electron Main Process
    Write-Host "Compiling Electron source..." -ForegroundColor Cyan
    npm run electron:build

    # 4. Packaging with electron-builder
    Write-Host "Running electron-builder for NSIS distribution..." -ForegroundColor Green
    npx electron-builder --win --config electron-builder.yml | Tee-Object -FilePath "nsis_build.log"

    Write-Host "`nBuild process finished. Check 'frontend/dist' for the installer." -ForegroundColor Green
}
catch {
    Write-Host "`nFATAL ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Details: $($_.ScriptStackTrace)" -ForegroundColor Gray
}
finally {
    Write-Host "`nPress any key to close this window..." -ForegroundColor Cyan
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
