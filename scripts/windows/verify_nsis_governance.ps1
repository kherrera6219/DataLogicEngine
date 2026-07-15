[CmdletBinding()]
Param(
    [string]$RepoRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepoRoot)) {
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

$configPath = Join-Path $RepoRoot "frontend\electron-builder.yml"
$packagePath = Join-Path $RepoRoot "frontend\package.json"
$versionAuthorityPath = Join-Path $RepoRoot "config\product-versions.json"
$nsisScriptPath = Join-Path $RepoRoot "frontend\electron\installer.nsh"

if (-not (Test-Path -LiteralPath $configPath)) {
    throw "NSIS governance check failed: missing $configPath"
}
if (-not (Test-Path -LiteralPath $packagePath)) {
    throw "NSIS governance check failed: missing $packagePath"
}
if (-not (Test-Path -LiteralPath $versionAuthorityPath)) {
    throw "NSIS governance check failed: missing $versionAuthorityPath"
}
if (-not (Test-Path -LiteralPath $nsisScriptPath)) {
    throw "NSIS governance check failed: missing $nsisScriptPath"
}

$configText = Get-Content -LiteralPath $configPath -Raw
$packageJson = Get-Content -LiteralPath $packagePath -Raw | ConvertFrom-Json
$versionAuthority = Get-Content -LiteralPath $versionAuthorityPath -Raw | ConvertFrom-Json
$nsisText = Get-Content -LiteralPath $nsisScriptPath -Raw

$checks = @(
    @{ id = "target_nsis"; pattern = "(?ms)win:\s*.*target:\s*.*-\s*nsis"; message = "Windows target must include NSIS." },
    @{ id = "copyright_kevin_herrera"; pattern = "(?m)^copyright:\s*Copyright © 2026 Kevin Herrera\s*$"; message = "Copyright metadata must use Kevin Herrera." },
    @{ id = "oneclick_disabled"; pattern = "(?m)^\s*oneClick:\s*false\s*$"; message = "oneClick must be false for enterprise governance." },
    @{ id = "per_machine"; pattern = "(?m)^\s*perMachine:\s*true\s*$"; message = "perMachine install must be enabled." },
    @{ id = "elevation_enabled"; pattern = "(?m)^\s*allowElevation:\s*true\s*$"; message = "allowElevation must be enabled." },
    @{ id = "change_install_dir"; pattern = "(?m)^\s*allowToChangeInstallationDirectory:\s*true\s*$"; message = "Installer must allow choosing the install directory." },
    @{ id = "desktop_shortcut"; pattern = "(?m)^\s*createDesktopShortcut:\s*always\s*$"; message = "Installer must create a desktop shortcut." },
    @{ id = "start_menu_shortcut"; pattern = "(?m)^\s*createStartMenuShortcut:\s*true\s*$"; message = "Installer must create a Start Menu shortcut." },
    @{ id = "uninstall_display_name"; pattern = '(?m)^\s*uninstallDisplayName:\s*"DataLogicEngine Desktop"\s*$'; message = "Uninstaller display name must be DataLogicEngine Desktop." },
    @{ id = "retain_app_data"; pattern = "(?m)^\s*deleteAppDataOnUninstall:\s*false\s*$"; message = "Uninstall must default to retaining app data." },
    @{ id = "run_after_finish"; pattern = "(?m)^\s*runAfterFinish:\s*true\s*$"; message = "Installer must show finish/run completion behavior." },
    @{ id = "update_signature_verification"; pattern = "(?m)^\s*verifyUpdateCodeSignature:\s*true\s*$"; message = "Electron update signature verification must be enabled." },
    @{ id = "versioned_artifact_name"; pattern = '(?m)^\s*artifactName:\s*"DataLogicEngine Setup \$\{version\}\.\$\{ext\}"\s*$'; message = "Installer artifact name must include the authoritative package version." },
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

$authorMatches = [string]$packageJson.author -eq "Kevin Herrera"
$results += [ordered]@{
    id = "package_author_kevin_herrera"
    passed = $authorMatches
    message = "Package author must be Kevin Herrera for Windows file metadata."
}
if (-not $authorMatches) {
    $failures += "Package author must be Kevin Herrera for Windows file metadata."
}

$versionMatches = [string]$packageJson.version -eq [string]$versionAuthority.product.version
$results += [ordered]@{
    id = "package_product_version"
    passed = $versionMatches
    message = "Frontend package version must match config/product-versions.json."
}
if (-not $versionMatches) {
    $failures += "Frontend package version must match config/product-versions.json."
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

$installLocationRegistered = [bool]($nsisText -match 'WriteRegStr\s+SHELL_CONTEXT\s+"\$\{UNINSTALL_REGISTRY_KEY\}"\s+"InstallLocation"\s+"\$INSTDIR"')
$results += [ordered]@{
    id = "registry_install_location"
    passed = $installLocationRegistered
    message = "Installer should write InstallLocation for Windows Apps metadata."
}
if (-not $installLocationRegistered) {
    $failures += "Installer should write InstallLocation for Windows Apps metadata."
}

$legacyScriptsExcluded = -not [bool]($configText -match '(?m)^\s*-\s+from:\s+\.\./scripts/windows\s*$')
$results += [ordered]@{
    id = "legacy_installer_scripts_excluded"
    passed = $legacyScriptsExcluded
    message = "Legacy standalone installer scripts must not be copied into the NSIS payload."
}
if (-not $legacyScriptsExcluded) {
    $failures += "Legacy standalone installer scripts must not be copied into the NSIS payload."
}

$report = [ordered]@{
    generated_at = [DateTime]::UtcNow.ToString("o")
    config_path = $configPath
    package_path = $packagePath
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
