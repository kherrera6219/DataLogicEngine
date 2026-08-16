# Verify packaged Electron resources required for desktop runtime.
# Run after electron:dist (expects frontend/dist/win-unpacked).

[CmdletBinding()]
Param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [string]$UnpackedRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $UnpackedRoot) {
    $UnpackedRoot = Join-Path $RepoRoot "frontend\dist\win-unpacked"
}

if (-not (Test-Path -LiteralPath $UnpackedRoot)) {
    throw "Packaging resources check failed: unpacked app not found at $UnpackedRoot"
}

$resources = Join-Path $UnpackedRoot "resources"
$required = @(
    (Join-Path $resources "backend\DataLogic_Backend.exe"),
    (Join-Path $resources "config\release-trust-policy.json"),
    (Join-Path $resources "config\release-channel.json")
)

# At least one rego policy if policies dir is shipped
$policiesDir = Join-Path $resources "policies"
$missing = @()
foreach ($path in $required) {
    if (-not (Test-Path -LiteralPath $path)) {
        $missing += $path
    }
}

$rego = @()
if (Test-Path -LiteralPath $policiesDir) {
    $rego = @(Get-ChildItem -Path $policiesDir -Filter "*.rego" -File -ErrorAction SilentlyContinue)
}
if ($rego.Count -lt 1) {
    $missing += "$policiesDir\*.rego (none found)"
}

$exe = Join-Path $UnpackedRoot "DataLogicEngine Desktop.exe"
if (-not (Test-Path -LiteralPath $exe)) {
    # productName may vary slightly; accept any .exe at root of unpacked
    $anyExe = Get-ChildItem -Path $UnpackedRoot -Filter "*.exe" -File -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notmatch "Uninstall" } |
        Select-Object -First 1
    if (-not $anyExe) {
        $missing += $exe
    }
}

$report = [ordered]@{
    generated_at = [DateTime]::UtcNow.ToString("o")
    unpacked_root = $UnpackedRoot
    resources_root = $resources
    required_checked = $required
    rego_count = $rego.Count
    missing = $missing
    ok = ($missing.Count -eq 0)
}

$reportDir = Join-Path $RepoRoot "reports"
if (-not (Test-Path $reportDir)) {
    New-Item -ItemType Directory -Path $reportDir | Out-Null
}
$reportPath = Join-Path $reportDir "packaging_resources_report.json"
($report | ConvertTo-Json -Depth 6) | Set-Content -Path $reportPath -Encoding utf8

if ($missing.Count -gt 0) {
    Write-Host "MISSING packaging resources:" -ForegroundColor Red
    $missing | ForEach-Object { Write-Host "  - $_" }
    throw "Packaging resources check failed with $($missing.Count) missing path(s). See $reportPath"
}

Write-Host "Packaging resources OK (rego=$($rego.Count)). Report: $reportPath" -ForegroundColor Green
