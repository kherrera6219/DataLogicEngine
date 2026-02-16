[CmdletBinding()]
Param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$configPath = Join-Path $RepoRoot "frontend\electron-builder.yml"
$nsisScriptPath = Join-Path $RepoRoot "frontend\electron\installer.nsh"

if (-not (Test-Path -LiteralPath $configPath)) {
    throw "NSIS governance check failed: missing $configPath"
}
if (-not (Test-Path -LiteralPath $nsisScriptPath)) {
    throw "NSIS governance check failed: missing $nsisScriptPath"
}

$configText = Get-Content -LiteralPath $configPath -Raw
$nsisText = Get-Content -LiteralPath $nsisScriptPath -Raw

$checks = @(
    @{ id = "target_nsis"; pattern = "(?ms)win:\s*.*target:\s*.*-\s*nsis"; message = "Windows target must include NSIS." },
    @{ id = "oneclick_disabled"; pattern = "(?m)^\s*oneClick:\s*false\s*$"; message = "oneClick must be false for enterprise governance." },
    @{ id = "per_machine"; pattern = "(?m)^\s*perMachine:\s*true\s*$"; message = "perMachine install must be enabled." },
    @{ id = "elevation_enabled"; pattern = "(?m)^\s*allowElevation:\s*true\s*$"; message = "allowElevation must be enabled." },
    @{ id = "retain_app_data"; pattern = "(?m)^\s*deleteAppDataOnUninstall:\s*false\s*$"; message = "Uninstall must default to retaining app data." },
    @{ id = "custom_nsis_include"; pattern = "(?m)^\s*include:\s*electron/installer\.nsh\s*$"; message = "Custom NSIS include must be present." }
)

$failures = @()
$results = @()
foreach ($check in $checks) {
    $matched = [bool]($configText -match $check.pattern)
    $results += [ordered]@{
        id = $check.id
        passed = $matched
        message = $check.message
    }
    if (-not $matched) {
        $failures += $check.message
    }
}

foreach ($macro in @("customHeader", "customInstall", "customUnInstall")) {
    $present = [bool]($nsisText -match ("!macro\s+" + [Regex]::Escape($macro)))
    $results += [ordered]@{
        id = "macro_$macro"
        passed = $present
        message = "NSIS macro '$macro' should be defined."
    }
    if (-not $present) {
        $failures += "NSIS macro '$macro' is missing from installer.nsh."
    }
}

$report = [ordered]@{
    generated_at = [DateTime]::UtcNow.ToString("o")
    config_path = $configPath
    nsis_script_path = $nsisScriptPath
    results = $results
    failures = $failures
}

$reportPath = Join-Path $RepoRoot "reports\nsis_governance_report.json"
New-Item -ItemType Directory -Path (Split-Path $reportPath) -Force | Out-Null
$report | ConvertTo-Json -Depth 6 | Set-Content -Path $reportPath -Encoding utf8

if ($failures.Count -gt 0) {
    throw "NSIS governance check failed: $($failures -join ' | ')"
}

Write-Host "NSIS governance check passed." -ForegroundColor Green
Write-Host "Report: $reportPath" -ForegroundColor Gray
