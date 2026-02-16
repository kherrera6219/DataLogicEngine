Param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [Parameter(Mandatory = $true)][string]$CertificatePath,
    [Parameter(Mandatory = $true)][string]$CertificatePassword,
    [string]$TimestampUrl = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $CertificatePath)) {
    throw "Certificate file not found: $CertificatePath"
}

$installers = Get-ChildItem -Path $RepoRoot -File -Filter "DataLogicEngine Setup *.exe" |
    Where-Object { $_.Name -notmatch "__uninstaller" }

if (-not $installers) {
    throw "No installer artifacts found in $RepoRoot"
}

$signtool = (Get-Command signtool.exe -ErrorAction SilentlyContinue | Select-Object -First 1).Source
if (-not $signtool) {
    throw "signtool.exe not found on PATH."
}

function Write-InstallerHash {
    Param(
        [Parameter(Mandatory = $true)][string]$FilePath
    )
    $leafName = Split-Path -Path $FilePath -Leaf
    $hashFile = "${FilePath}.sha256"
    $hashValue = (Get-FileHash -LiteralPath $FilePath -Algorithm SHA256).Hash.ToLowerInvariant()
    "$hashValue  $leafName" | Set-Content -Path $hashFile -Encoding ascii
}

foreach ($installer in $installers) {
    Write-Host "Signing $($installer.Name)..." -ForegroundColor Cyan
    & $signtool sign `
        /fd SHA256 `
        /f $CertificatePath `
        /p $CertificatePassword `
        /tr $TimestampUrl `
        /td SHA256 `
        /d "DataLogicEngine" `
        $installer.FullName

    if ($LASTEXITCODE -ne 0) {
        throw "signtool failed for $($installer.Name) with exit code $LASTEXITCODE"
    }

    Write-InstallerHash -FilePath $installer.FullName
}

$verifyScript = Join-Path $PSScriptRoot "verify_installer_signature.ps1"
& powershell -NoProfile -ExecutionPolicy Bypass -File $verifyScript -RepoRoot $RepoRoot -RequireArtifacts

if ($LASTEXITCODE -ne 0) {
    throw "Post-signature verification failed."
}

Write-Host "Installer signing completed successfully." -ForegroundColor Green
