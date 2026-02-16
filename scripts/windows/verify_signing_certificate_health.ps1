Param(
    [Parameter(Mandatory = $true)][string]$CertificatePath,
    [Parameter(Mandatory = $true)][string]$CertificatePassword,
    [int]$MinDaysRemaining = 60,
    [switch]$CheckRevocation,
    [string]$ReportPath = "reports/codesigning_certificate_health.json"
)

$ErrorActionPreference = "Stop"
$codeSigningOid = "1.3.6.1.5.5.7.3.3"

if (-not (Test-Path $CertificatePath)) {
    throw "Certificate file not found: $CertificatePath"
}

function Get-CertificateStatus {
    Param(
        [Parameter(Mandatory = $true)][System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificate,
        [switch]$CheckRevocation
    )

    $now = [DateTime]::UtcNow
    $daysRemaining = [math]::Floor(($Certificate.NotAfter.ToUniversalTime() - $now).TotalDays)

    $ekuOids = @()
    foreach ($eku in $Certificate.EnhancedKeyUsageList) {
        $ekuOids += [string]$eku.Value
    }
    $hasCodeSigningEku = $ekuOids -contains $codeSigningOid

    $revocation = [ordered]@{
        checked = [bool]$CheckRevocation
        valid = $null
        chain_status = @()
    }

    if ($CheckRevocation) {
        $chain = New-Object System.Security.Cryptography.X509Certificates.X509Chain
        $chain.ChainPolicy.RevocationMode = [System.Security.Cryptography.X509Certificates.X509RevocationMode]::Online
        $chain.ChainPolicy.RevocationFlag = [System.Security.Cryptography.X509Certificates.X509RevocationFlag]::EntireChain
        $chain.ChainPolicy.VerificationFlags = [System.Security.Cryptography.X509Certificates.X509VerificationFlags]::NoFlag
        $chain.ChainPolicy.UrlRetrievalTimeout = [TimeSpan]::FromSeconds(15)
        $revocation.valid = [bool]$chain.Build($Certificate)
        foreach ($status in $chain.ChainStatus) {
            $revocation.chain_status += [ordered]@{
                status = [string]$status.Status
                info = ([string]$status.StatusInformation).Trim()
            }
        }
    }

    return [ordered]@{
        subject = [string]$Certificate.Subject
        thumbprint = [string]$Certificate.Thumbprint
        not_before = $Certificate.NotBefore.ToUniversalTime().ToString("o")
        not_after = $Certificate.NotAfter.ToUniversalTime().ToString("o")
        days_remaining = $daysRemaining
        has_code_signing_eku = [bool]$hasCodeSigningEku
        revocation = $revocation
        eku_oids = $ekuOids
    }
}

$securePassword = ConvertTo-SecureString -String $CertificatePassword -AsPlainText -Force
$cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2
$cert.Import($CertificatePath, $securePassword, [System.Security.Cryptography.X509Certificates.X509KeyStorageFlags]::Exportable)

$status = Get-CertificateStatus -Certificate $cert -CheckRevocation:$CheckRevocation
$failures = @()

if ([int]$status.days_remaining -lt [int]$MinDaysRemaining) {
    $failures += "Certificate expires in $($status.days_remaining) day(s), below threshold $MinDaysRemaining."
}

if (-not [bool]$status.has_code_signing_eku) {
    $failures += "Certificate is missing Code Signing EKU ($codeSigningOid)."
}

if ($CheckRevocation -and ($status.revocation.valid -ne $true)) {
    $failures += "Certificate revocation/chain validation failed."
}

$report = [ordered]@{
    generated_at = [DateTime]::UtcNow.ToString("o")
    certificate_path = $CertificatePath
    minimum_days_remaining = [int]$MinDaysRemaining
    status = $status
    failures = $failures
}

New-Item -ItemType Directory -Path (Split-Path $ReportPath) -Force | Out-Null
$report | ConvertTo-Json -Depth 8 | Set-Content -Path $ReportPath -Encoding utf8

if ($failures.Count -gt 0) {
    Write-Error "Code-signing certificate health check failed: $($failures -join '; ')"
    Write-Host "Report: $ReportPath" -ForegroundColor Yellow
    exit 1
}

Write-Host "Code-signing certificate health check passed." -ForegroundColor Green
Write-Host "Report: $ReportPath" -ForegroundColor Green
