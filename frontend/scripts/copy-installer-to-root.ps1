Param(
    [string]$RepoRoot
)

$ErrorActionPreference = "Stop"

$FrontendRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (-not $RepoRoot) {
    $RepoRoot = (Resolve-Path (Join-Path $FrontendRoot "..")).Path
}

$DistDir = Join-Path $FrontendRoot "dist"
if (-not (Test-Path $DistDir)) {
    throw "Installer output directory not found: $DistDir"
}

$Installer = Get-ChildItem -Path $DistDir -File -Filter "DataLogicEngine Setup *.exe" |
    Where-Object { $_.Name -notmatch "__uninstaller" } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $Installer) {
    throw "No installer executable found in $DistDir"
}

$RepoInstaller = Join-Path $RepoRoot $Installer.Name
Copy-Item -Path $Installer.FullName -Destination $RepoInstaller -Force

$LatestInstallerAlias = Join-Path $RepoRoot "DataLogicEngine Setup Latest.exe"
Copy-Item -Path $Installer.FullName -Destination $LatestInstallerAlias -Force

$BlockMap = "$($Installer.FullName).blockmap"
if (Test-Path $BlockMap) {
    Copy-Item -Path $BlockMap -Destination "${RepoInstaller}.blockmap" -Force
    Copy-Item -Path $BlockMap -Destination (Join-Path $RepoRoot "DataLogicEngine Setup Latest.exe.blockmap") -Force
}

# Keep repo root focused on the latest installer and alias only.
Get-ChildItem -Path $RepoRoot -File -Filter "DataLogicEngine Setup *.exe" |
    Where-Object { $_.FullName -ne $RepoInstaller -and $_.FullName -ne $LatestInstallerAlias } |
    Remove-Item -Force -ErrorAction SilentlyContinue

Get-ChildItem -Path $RepoRoot -File -Filter "DataLogicEngine Setup *.exe.blockmap" |
    Where-Object {
        $_.FullName -ne "${RepoInstaller}.blockmap" -and
        $_.FullName -ne (Join-Path $RepoRoot "DataLogicEngine Setup Latest.exe.blockmap")
    } |
    Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "Installer copied to repo root: $RepoInstaller" -ForegroundColor Green
Write-Host "Installer alias updated: $LatestInstallerAlias" -ForegroundColor Green
