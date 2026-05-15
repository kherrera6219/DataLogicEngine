Param(
    [string]$Subject = "CN=Kevin Herrera",
    [string]$OutputPath,
    [Parameter(Mandatory = $true)][string]$Password,
    [int]$YearsValid = 2,
    [switch]$TrustForCurrentUser
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
    $OutputPath = Join-Path $repoRoot "certs\dev-codesign-kevin-herrera.pfx"
}

$outputDirectory = Split-Path -Path $OutputPath -Parent
if ($outputDirectory) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

$securePassword = ConvertTo-SecureString -String $Password -AsPlainText -Force
$certificate = New-SelfSignedCertificate `
    -Subject $Subject `
    -Type CodeSigningCert `
    -KeyAlgorithm RSA `
    -KeyLength 3072 `
    -HashAlgorithm SHA256 `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -NotAfter (Get-Date).AddYears($YearsValid)

Export-PfxCertificate `
    -Cert $certificate `
    -FilePath $OutputPath `
    -Password $securePassword `
    -Force | Out-Null

if ($TrustForCurrentUser) {
    $trustedRootStore = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "CurrentUser")
    try {
        $trustedRootStore.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
        $trustedRootStore.Add($certificate)
    }
    finally {
        $trustedRootStore.Close()
    }
}

Write-Host "Development code-signing certificate created: $OutputPath" -ForegroundColor Green
Write-Host "Subject: $($certificate.Subject)" -ForegroundColor Green
Write-Host "Thumbprint: $($certificate.Thumbprint)" -ForegroundColor Green
Write-Host "Expires: $($certificate.NotAfter.ToUniversalTime().ToString("o"))" -ForegroundColor Green
if ($TrustForCurrentUser) {
    Write-Host "Certificate trusted for the current user. Use only for local validation." -ForegroundColor Yellow
}
else {
    Write-Host "Certificate was not trusted. Signatures will verify as self-signed unless you trust the certificate locally." -ForegroundColor Yellow
}
