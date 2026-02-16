Param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [switch]$RequireArtifacts
)

$ErrorActionPreference = "Stop"

$installers = Get-ChildItem -Path $RepoRoot -File -Filter "DataLogicEngine Setup *.exe" |
    Where-Object { $_.Name -notmatch "__uninstaller" }

if (-not $installers -and $RequireArtifacts) {
    throw "No installer artifacts found in $RepoRoot"
}

$failures = @()
$results = @()

foreach ($installer in $installers) {
    $signature = Get-AuthenticodeSignature -FilePath $installer.FullName
    $row = [ordered]@{
        artifact = $installer.Name
        status = [string]$signature.Status
        signer = if ($signature.SignerCertificate) { $signature.SignerCertificate.Subject } else { "" }
        thumbprint = if ($signature.SignerCertificate) { $signature.SignerCertificate.Thumbprint } else { "" }
    }
    $results += $row

    if ($signature.Status -ne 'Valid') {
        $failures += "$($installer.Name): $($signature.Status)"
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
