Param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [switch]$RequireArtifacts,
    [switch]$CheckRevocation
)

$ErrorActionPreference = "Stop"

$installers = Get-ChildItem -Path $RepoRoot -File -Filter "DataLogicEngine Setup *.exe" |
    Where-Object { $_.Name -notmatch "__uninstaller" }

if (-not $installers -and $RequireArtifacts) {
    throw "No installer artifacts found in $RepoRoot"
}

$failures = @()
$results = @()

function Test-CertificateRevocation {
    Param(
        [Parameter(Mandatory = $true)][System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificate
    )

    $chain = New-Object System.Security.Cryptography.X509Certificates.X509Chain
    $chain.ChainPolicy.RevocationMode = [System.Security.Cryptography.X509Certificates.X509RevocationMode]::Online
    $chain.ChainPolicy.RevocationFlag = [System.Security.Cryptography.X509Certificates.X509RevocationFlag]::EntireChain
    $chain.ChainPolicy.VerificationFlags = [System.Security.Cryptography.X509Certificates.X509VerificationFlags]::NoFlag
    $chain.ChainPolicy.UrlRetrievalTimeout = [TimeSpan]::FromSeconds(15)
    $isValid = [bool]$chain.Build($Certificate)
    $statuses = @()
    foreach ($status in $chain.ChainStatus) {
        $statuses += [ordered]@{
            status = [string]$status.Status
            info = ([string]$status.StatusInformation).Trim()
        }
    }
    return [ordered]@{
        valid = $isValid
        statuses = $statuses
    }
}

foreach ($installer in $installers) {
    $signature = Get-AuthenticodeSignature -FilePath $installer.FullName
    $revocationResult = $null
    if ($CheckRevocation -and $signature.SignerCertificate) {
        $revocationResult = Test-CertificateRevocation -Certificate $signature.SignerCertificate
    }
    $row = [ordered]@{
        artifact = $installer.Name
        status = [string]$signature.Status
        signer = if ($signature.SignerCertificate) { $signature.SignerCertificate.Subject } else { "" }
        thumbprint = if ($signature.SignerCertificate) { $signature.SignerCertificate.Thumbprint } else { "" }
        revocation_checked = [bool]$CheckRevocation
        revocation_valid = if ($revocationResult) { [bool]$revocationResult.valid } else { $null }
        revocation_statuses = if ($revocationResult) { $revocationResult.statuses } else { @() }
    }
    $results += $row

    if ($signature.Status -ne 'Valid') {
        $failures += "$($installer.Name): $($signature.Status)"
    }
    if ($CheckRevocation -and $revocationResult -and ($revocationResult.valid -ne $true)) {
        $failures += "$($installer.Name): certificate revocation/chain validation failed"
    }
}

$reportPath = Join-Path $RepoRoot "reports\installer_signature_report.json"
New-Item -ItemType Directory -Path (Split-Path $reportPath) -Force | Out-Null
$payload = @{
    generated_at = [DateTime]::UtcNow.ToString("o")
    repo_root = $RepoRoot
    artifacts = $results
    failures = $failures
}
$payload | ConvertTo-Json -Depth 5 | Set-Content -Path $reportPath -Encoding utf8

if ($failures.Count -gt 0) {
    Write-Error "Installer signature verification failed: $($failures -join '; ')"
    exit 1
}

Write-Host "Installer signature verification passed for $($results.Count) artifact(s)." -ForegroundColor Green
Write-Host "Report: $reportPath" -ForegroundColor Green
