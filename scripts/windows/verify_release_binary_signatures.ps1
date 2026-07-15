[CmdletBinding()]
Param(
    [string]$RepoRoot,
    [string]$ReportPath = "reports\production-readiness\2026\phase-14\binary-signature-inventory.json",
    [switch]$RequireComplete,
    [switch]$CheckRevocation
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

$trustPolicyPath = Join-Path $RepoRoot "config\release-trust-policy.json"
if (-not (Test-Path -LiteralPath $trustPolicyPath)) {
    throw "Release trust policy is missing: $trustPolicyPath"
}
$trustPolicy = Get-Content -LiteralPath $trustPolicyPath -Raw | ConvertFrom-Json
$approvedPublisherSubjects = @($trustPolicy.signing.expected_publisher_subjects)

$versionAuthorityPath = Join-Path $RepoRoot "config\product-versions.json"
$versionAuthority = Get-Content -LiteralPath $versionAuthorityPath -Raw | ConvertFrom-Json
$installerName = "DataLogicEngine Setup $([string]$versionAuthority.product.version).exe"
$installerPath = Join-Path $RepoRoot $installerName
$payloadRoots = @(
    (Join-Path $RepoRoot "dist\DataLogic_Backend"),
    (Join-Path $RepoRoot "frontend\dist\win-unpacked")
)
$normalizedRepoRoot = [IO.Path]::GetFullPath($RepoRoot).TrimEnd([char[]]@([char]92, [char]47))

function Get-RepoRelativePath([string]$Path) {
    $normalizedPath = [IO.Path]::GetFullPath($Path)
    $rootPrefix = "$normalizedRepoRoot$([IO.Path]::DirectorySeparatorChar)"
    if ($normalizedPath.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        return $normalizedPath.Substring($rootPrefix.Length)
    }
    return $normalizedPath
}

$candidates = @()
if (Test-Path -LiteralPath $installerPath) {
    $candidates += Get-Item -LiteralPath $installerPath
}
foreach ($payloadRoot in $payloadRoots) {
    if (Test-Path -LiteralPath $payloadRoot) {
        $candidates += Get-ChildItem -LiteralPath $payloadRoot -Recurse -File |
            Where-Object { $_.Extension -in @(".exe", ".dll", ".ps1") }
    }
}
$candidates = @($candidates | Sort-Object FullName -Unique)

function Test-CertificateChain(
    [System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificate
) {
    if (-not $Certificate) { return $false }
    $chain = [System.Security.Cryptography.X509Certificates.X509Chain]::new()
    $chain.ChainPolicy.RevocationMode = [System.Security.Cryptography.X509Certificates.X509RevocationMode]::Online
    $chain.ChainPolicy.RevocationFlag = [System.Security.Cryptography.X509Certificates.X509RevocationFlag]::EntireChain
    $chain.ChainPolicy.UrlRetrievalTimeout = [TimeSpan]::FromSeconds(15)
    return [bool]$chain.Build($Certificate)
}

$rows = @()
$failures = @()
foreach ($candidate in $candidates) {
    $signature = Get-AuthenticodeSignature -LiteralPath $candidate.FullName
    $relativePath = Get-RepoRelativePath -Path $candidate.FullName
    $appOwned = $candidate.Name -in @(
        $installerName,
        "DataLogic_Backend.exe",
        "DataLogicEngine Desktop.exe"
    )
    $subject = if ($signature.SignerCertificate) {
        [string]$signature.SignerCertificate.Subject
    } else { "" }
    $publisherMatch = if ($appOwned -and $approvedPublisherSubjects.Count -gt 0) {
        $approvedPublisherSubjects -contains $subject
    } elseif ($appOwned) {
        $false
    } else {
        $null
    }
    $revocationValid = if ($CheckRevocation -and $signature.SignerCertificate) {
        Test-CertificateChain -Certificate $signature.SignerCertificate
    } else { $null }
    $valid = $signature.Status -eq "Valid"
    if ($appOwned) {
        $valid = $valid -and ($publisherMatch -eq $true)
    }
    if ($CheckRevocation) {
        $valid = $valid -and ($revocationValid -eq $true)
    }
    if (-not $valid) {
        $failures += "$relativePath signature or publisher trust failed"
    }
    $rows += [ordered]@{
        path = $relativePath
        sha256 = (Get-FileHash -LiteralPath $candidate.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        app_owned = $appOwned
        signature_status = [string]$signature.Status
        signer_subject = $subject
        publisher_match = $publisherMatch
        revocation_checked = [bool]$CheckRevocation
        revocation_valid = $revocationValid
        valid = $valid
    }
}

if (-not (Test-Path -LiteralPath $installerPath)) {
    $failures += "canonical installer is missing: $installerName"
}
foreach ($payloadRoot in $payloadRoots) {
    if (-not (Test-Path -LiteralPath $payloadRoot)) {
        $failures += "release payload root is missing: $payloadRoot"
    }
}
if ($approvedPublisherSubjects.Count -eq 0) {
    $failures += "approved publisher subject is not configured"
}

$payload = [ordered]@{
    schema_version = "dle.binary-signature-inventory.v1"
    generated_at = [DateTime]::UtcNow.ToString("o")
    status = if ($failures.Count -eq 0) { "pass" } else { "fail" }
    expected_installer = $installerName
    approved_publisher_subjects = $approvedPublisherSubjects
    artifacts = $rows
    failures = $failures
}
$resolvedReportPath = if ([IO.Path]::IsPathRooted($ReportPath)) {
    $ReportPath
} else {
    Join-Path $RepoRoot $ReportPath
}
New-Item -ItemType Directory -Path (Split-Path $resolvedReportPath) -Force | Out-Null
$payload | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resolvedReportPath -Encoding utf8

Write-Host "Binary signature inventory: $($payload.status), artifacts=$($rows.Count)" -ForegroundColor Cyan
Write-Host "Report: $resolvedReportPath" -ForegroundColor Gray
if ($RequireComplete -and $failures.Count -gt 0) {
    throw "Release binary signature inventory failed: $($failures -join ' | ')"
}
