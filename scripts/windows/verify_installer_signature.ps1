Param(
    [string]$RepoRoot,
    [switch]$RequireArtifacts,
    [switch]$CheckRevocation,
    [switch]$RequireProductionTrust
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

$versionAuthorityPath = Join-Path $RepoRoot "config\product-versions.json"
if (-not (Test-Path -LiteralPath $versionAuthorityPath)) {
    throw "Product version authority is missing: $versionAuthorityPath"
}
$versionAuthority = Get-Content -LiteralPath $versionAuthorityPath -Raw | ConvertFrom-Json
$expectedInstallerName = "DataLogicEngine Setup $([string]$versionAuthority.product.version).exe"

$trustPolicyPath = Join-Path $RepoRoot "config\release-trust-policy.json"
$approvedPublisherSubjects = @()
$trustedTimestampRequired = $false
if ($RequireProductionTrust) {
    if (-not (Test-Path -LiteralPath $trustPolicyPath)) {
        throw "Release trust policy is missing: $trustPolicyPath"
    }
    $trustPolicy = Get-Content -LiteralPath $trustPolicyPath -Raw | ConvertFrom-Json
    if ($trustPolicy.schema_version -ne "dle.release-trust-policy.v1") {
        throw "Release trust policy schema is invalid."
    }
    if ($trustPolicy.signing.production_authorized -ne $true) {
        throw "Production publisher signing is not authorized by release trust policy."
    }
    $approvedPublisherSubjects = @($trustPolicy.signing.expected_publisher_subjects)
    if ($approvedPublisherSubjects.Count -eq 0) {
        throw "Release trust policy does not declare an approved publisher subject."
    }
    $trustedTimestampRequired = [bool]$trustPolicy.signing.trusted_timestamp_required
}

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
    if ($installer.Name -ne $expectedInstallerName) {
        $failures += "$($installer.Name): expected canonical artifact $expectedInstallerName"
    }
    $signature = Get-AuthenticodeSignature -FilePath $installer.FullName
    $revocationResult = $null
    if ($CheckRevocation -and $signature.SignerCertificate) {
        $revocationResult = Test-CertificateRevocation -Certificate $signature.SignerCertificate
    }
    $row = [ordered]@{
        artifact = $installer.Name
        status = [string]$signature.Status
        signer = if ($signature.SignerCertificate) { $signature.SignerCertificate.Subject } else { "" }
        timestamp_signer = if ($signature.TimeStamperCertificate) { $signature.TimeStamperCertificate.Subject } else { "" }
        thumbprint = if ($signature.SignerCertificate) { $signature.SignerCertificate.Thumbprint } else { "" }
        publisher_match = if ($RequireProductionTrust -and $signature.SignerCertificate) {
            $approvedPublisherSubjects -contains $signature.SignerCertificate.Subject
        } else { $null }
        revocation_checked = [bool]$CheckRevocation
        revocation_valid = if ($revocationResult) { [bool]$revocationResult.valid } else { $null }
        revocation_statuses = if ($revocationResult) { $revocationResult.statuses } else { @() }
    }
    $results += $row

    if ($signature.Status -ne 'Valid') {
        $failures += "$($installer.Name): $($signature.Status)"
    }
    if ($RequireProductionTrust -and $signature.SignerCertificate -and
        ($approvedPublisherSubjects -notcontains $signature.SignerCertificate.Subject)) {
        $failures += "$($installer.Name): signer subject is not an approved publisher"
    }
    if ($RequireProductionTrust -and $trustedTimestampRequired -and -not $signature.TimeStamperCertificate) {
        $failures += "$($installer.Name): trusted timestamp is required but missing"
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
    expected_installer = $expectedInstallerName
    production_trust_required = [bool]$RequireProductionTrust
    approved_publisher_subjects = $approvedPublisherSubjects
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
