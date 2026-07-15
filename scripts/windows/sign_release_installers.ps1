Param(
    [string]$RepoRoot,
    [Parameter(Mandatory = $true)][string]$CertificatePath,
    [Parameter(Mandatory = $true)][string]$CertificatePassword,
    [string]$TimestampUrl = "http://timestamp.digicert.com",
    [int]$MinimumCertificateDaysRemaining = 45,
    [switch]$CheckCertificateRevocation,
    [switch]$CheckSignatureRevocation
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

if (-not (Test-Path $CertificatePath)) {
    throw "Certificate file not found: $CertificatePath"
}

$certificateHealthScript = Join-Path $PSScriptRoot "verify_signing_certificate_health.ps1"
if (-not (Test-Path $certificateHealthScript)) {
    throw "Certificate health verification script not found: $certificateHealthScript"
}

$certificateHealthArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $certificateHealthScript,
    "-CertificatePath", $CertificatePath,
    "-CertificatePassword", $CertificatePassword,
    "-MinDaysRemaining", $MinimumCertificateDaysRemaining
)
if ($CheckCertificateRevocation) {
    $certificateHealthArgs += "-CheckRevocation"
}
& powershell @certificateHealthArgs

if ($LASTEXITCODE -ne 0) {
    throw "Certificate health verification failed."
}

$installers = Get-ChildItem -Path $RepoRoot -File -Filter "DataLogicEngine Setup *.exe" |
    Where-Object { $_.Name -notmatch "__uninstaller" }

if (-not $installers) {
    throw "No installer artifacts found in $RepoRoot"
}

function Get-SignToolPath {
    $pathCommand = Get-Command signtool.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($pathCommand) {
        return $pathCommand.Source
    }

    $candidatePaths = @(
        (Join-Path $RepoRoot "frontend\node_modules\@electron\windows-sign\vendor\signtool.exe"),
        (Join-Path $RepoRoot "frontend\node_modules\electron-winstaller\vendor\signtool.exe"),
        (Join-Path $env:LOCALAPPDATA "electron-builder\Cache\winCodeSign\winCodeSign-2.6.0\windows-10\x64\signtool.exe")
    )

    foreach ($candidatePath in $candidatePaths) {
        if (Test-Path -LiteralPath $candidatePath) {
            return $candidatePath
        }
    }

    return $null
}

$signtool = Get-SignToolPath
if (-not $signtool) {
    throw "signtool.exe not found on PATH or known local build-tool paths."
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
$verifyArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $verifyScript,
    "-RepoRoot", $RepoRoot,
    "-RequireArtifacts",
    "-RequireProductionTrust"
)
if ($CheckSignatureRevocation) {
    $verifyArgs += "-CheckRevocation"
}
& powershell @verifyArgs

if ($LASTEXITCODE -ne 0) {
    throw "Post-signature verification failed."
}

Write-Host "Installer signing completed successfully." -ForegroundColor Green
