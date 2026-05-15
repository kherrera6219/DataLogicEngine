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

$CanonicalInstallerName = "DataLogicEngine Setup Latest.exe"
$Installer = Get-ChildItem -Path $DistDir -File -Filter $CanonicalInstallerName |
    Select-Object -First 1

if (-not $Installer) {
    throw "No canonical installer executable found in $DistDir"
}

$RepoInstaller = Join-Path $RepoRoot $CanonicalInstallerName
Copy-Item -Path $Installer.FullName -Destination $RepoInstaller -Force

function Write-InstallerHash {
    Param(
        [Parameter(Mandatory = $true)][string]$FilePath
    )

    $LeafName = Split-Path -Path $FilePath -Leaf
    $HashFile = "${FilePath}.sha256"
    $Sha256 = [System.Security.Cryptography.SHA256]::Create()
    $Stream = [System.IO.File]::OpenRead($FilePath)
    try {
        $HashBytes = $Sha256.ComputeHash($Stream)
    }
    finally {
        $Stream.Dispose()
        $Sha256.Dispose()
    }
    $HashValue = -join ($HashBytes | ForEach-Object { $_.ToString("x2") })
    "$HashValue  $LeafName" | Set-Content -Path $HashFile -Encoding ascii
    return $HashFile
}

$BlockMap = "$($Installer.FullName).blockmap"
if (Test-Path $BlockMap) {
    Copy-Item -Path $BlockMap -Destination "${RepoInstaller}.blockmap" -Force
}

$RepoInstallerHash = Write-InstallerHash -FilePath $RepoInstaller

# Keep the repo root focused on the single canonical installer.
Get-ChildItem -Path $RepoRoot -File -Filter "DataLogicEngine Setup *.exe" |
    Where-Object { $_.FullName -ne $RepoInstaller } |
    Remove-Item -Force -ErrorAction SilentlyContinue

Get-ChildItem -Path $RepoRoot -File -Filter "DataLogicEngine Setup *.exe.blockmap" |
    Where-Object { $_.FullName -ne "${RepoInstaller}.blockmap" } |
    Remove-Item -Force -ErrorAction SilentlyContinue

Get-ChildItem -Path $RepoRoot -File -Filter "DataLogicEngine Setup *.exe.sha256" |
    Where-Object { $_.FullName -ne "${RepoInstaller}.sha256" } |
    Remove-Item -Force -ErrorAction SilentlyContinue

# The signed, user-facing installer lives at the repo root. Remove transient
# setup copies from frontend/dist so the checkout never shows two app installers.
Get-ChildItem -Path $DistDir -File -Filter "DataLogicEngine Setup *.exe" |
    Remove-Item -Force -ErrorAction SilentlyContinue

Get-ChildItem -Path $DistDir -File -Filter "DataLogicEngine Setup *.exe.blockmap" |
    Remove-Item -Force -ErrorAction SilentlyContinue

Write-Host "Installer copied to repo root: $RepoInstaller" -ForegroundColor Green
Write-Host "Installer checksum written: $RepoInstallerHash" -ForegroundColor Green
