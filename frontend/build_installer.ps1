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
    $hasCodeSigningMaterial = [bool]($env:CSC_LINK) -or [bool]($env:WIN_CSC_LINK)
    if ($hasCodeSigningMaterial) {
        Write-Host "Code signing material detected. Enabling signed build mode..." -ForegroundColor Yellow
        Remove-Item Env:CSC_SKIP -ErrorAction SilentlyContinue
    }
    else {
        Write-Host "No code signing material detected. Building unsigned installer..." -ForegroundColor Yellow
        $env:CSC_SKIP = "true"
    }

    # 2. Rebuild the Python backend (PyInstaller) so the packaged app always
    #    ships the current backend code. Skipping this caused the installer to
    #    bundle a stale backend (missing endpoints, inactive fixes).
    Write-Host "Rebuilding Python backend (PyInstaller)..." -ForegroundColor Cyan
    $RepoRoot = "c:\software\DataLogicEngine"
    $BackendPy = $null
    foreach ($cand in @("$RepoRoot\.venv311\Scripts\python.exe", "$RepoRoot\.venv\Scripts\python.exe")) {
        if (Test-Path $cand) { $BackendPy = $cand; break }
    }
    if (-not $BackendPy) {
        Write-Host "WARNING: No project venv python found; skipping backend rebuild." -ForegroundColor Yellow
    }
    else {
        Push-Location $RepoRoot
        try {
            & $BackendPy scripts\build_backend.py
            if ($LASTEXITCODE -ne 0) { throw "Backend build failed (exit $LASTEXITCODE)" }
            if (-not (Test-Path "$RepoRoot\dist\DataLogic_Backend\DataLogic_Backend.exe")) {
                throw "Backend executable not produced"
            }
            Write-Host "Backend rebuilt successfully." -ForegroundColor Green
        }
        finally {
            Pop-Location
        }
    }

    # 3. Re-trigger Next.js Build (Ensure up to date)
    Write-Host "Running Next.js production build..." -ForegroundColor Cyan
    npm run build

    # 4. Compiling Electron Main Process
    Write-Host "Compiling Electron source..." -ForegroundColor Cyan
    npm run electron:build

    # 4b. Re-apply electron-builder npm-collector patch (Windows + NVM)
    Write-Host "Applying electron-builder npm-collector patch..." -ForegroundColor Cyan
    npm run fix:eb

    # 4. Packaging with electron-builder
    Write-Host "Running electron-builder for NSIS distribution..." -ForegroundColor Green
    npx electron-builder --win --config electron-builder.yml | Tee-Object -FilePath "nsis_build.log"

    # 5. Copy installer to repository root for easier manual discovery
    $CopyScript = Join-Path $PSScriptRoot "scripts\copy-installer-to-root.ps1"
    if (Test-Path $CopyScript) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $CopyScript
    }
    else {
        Write-Host "Warning: copy-installer-to-root script not found at $CopyScript" -ForegroundColor Yellow
    }

    Write-Host "`nBuild process finished. Installer is available in repo root and frontend/dist." -ForegroundColor Green
}
catch {
    Write-Host "`nFATAL ERROR: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Details: $($_.ScriptStackTrace)" -ForegroundColor Gray
}
finally {
    Write-Host "`nPress any key to close this window..." -ForegroundColor Cyan
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
