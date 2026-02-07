[CmdletBinding()]
Param(
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$DeployDir = Join-Path $RepoRoot "deploy\windows"
$WinSWPath = Join-Path $DeployDir "winsw.exe"
$WinSWUrl = "https://github.com/winsw/winsw/releases/latest/download/WinSW-x64.exe"

Write-Host "--- Preparing WiX/WinSW Assets ---" -ForegroundColor Cyan

if (-not (Test-Path -LiteralPath $DeployDir)) {
    New-Item -ItemType Directory -Path $DeployDir | Out-Null
}

if ((Test-Path -LiteralPath $WinSWPath) -and -not $Force) {
    Write-Host "[PASS] WinSW already present at $WinSWPath" -ForegroundColor Green
}
else {
    Write-Host "[INFO] Downloading WinSW to $WinSWPath" -ForegroundColor Yellow
    Invoke-WebRequest -Uri $WinSWUrl -OutFile $WinSWPath -UseBasicParsing
    $downloaded = Get-Item -LiteralPath $WinSWPath
    if ($downloaded.Length -le 0) {
        throw "Downloaded WinSW file is empty: $WinSWPath"
    }
    Write-Host "[PASS] WinSW downloaded ($($downloaded.Length) bytes)" -ForegroundColor Green
}

$backendExe = Join-Path $RepoRoot "dist\DataLogic_Backend\DataLogic_Backend.exe"
$frontendServer = Join-Path $RepoRoot "frontend\.next\standalone\server.js"

if (Test-Path -LiteralPath $backendExe) {
    Write-Host "[PASS] Backend artifact found: $backendExe" -ForegroundColor Green
}
else {
    Write-Host "[WARN] Backend artifact missing: $backendExe" -ForegroundColor Yellow
    Write-Host "       Build it before WiX packaging (PyInstaller backend build)." -ForegroundColor Yellow
}

if (Test-Path -LiteralPath $frontendServer) {
    Write-Host "[PASS] Frontend standalone server found: $frontendServer" -ForegroundColor Green
}
else {
    Write-Host "[WARN] Frontend standalone artifact missing: $frontendServer" -ForegroundColor Yellow
    Write-Host "       Build standalone frontend before WiX packaging." -ForegroundColor Yellow
}

Write-Host "WiX asset preparation complete." -ForegroundColor Cyan
