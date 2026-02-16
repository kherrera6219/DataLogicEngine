[CmdletBinding()]
Param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [string]$InstallPath = (Join-Path $env:ProgramFiles "DataLogicEngine"),
    [int]$TimeoutSeconds = 240
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$installer = Get-ChildItem -Path $RepoRoot -File -Filter "DataLogicEngine Setup *.exe" |
    Where-Object { $_.Name -notmatch "__uninstaller" } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $installer) {
    throw "Silent install failed: no installer artifact found in $RepoRoot"
}

Write-Host "Starting silent installation from: $($installer.FullName)" -ForegroundColor Cyan
Write-Host "Install path: $InstallPath" -ForegroundColor Cyan

$process = Start-Process -FilePath $installer.FullName -ArgumentList @("/S", "/D=$InstallPath") -PassThru
$finished = $process.WaitForExit($TimeoutSeconds * 1000)
if (-not $finished) {
    Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
    throw "Silent installation timed out after $TimeoutSeconds seconds."
}

if ($process.ExitCode -ne 0) {
    throw "Silent installation failed with exit code $($process.ExitCode)."
}

Write-Host "Silent installation completed successfully." -ForegroundColor Green
