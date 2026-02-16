[CmdletBinding()]
Param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [ValidateSet("portable", "installer")]
    [string]$Mode = "portable",
    [switch]$SkipUninstall,
    [int]$LaunchTimeoutSeconds = 25,
    [int]$InstallTimeoutSeconds = 240,
    [int]$UninstallTimeoutSeconds = 180
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Find-LatestInstaller([string]$RootPath) {
    return Get-ChildItem -Path $RootPath -File -Filter "DataLogicEngine Setup *.exe" |
        Where-Object { $_.Name -notmatch "__uninstaller" } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
}

function Find-Uninstaller([string]$InstallPath) {
    $patterns = @("Uninstall*.exe", "unins*.exe")
    foreach ($pattern in $patterns) {
        $candidate = Get-ChildItem -Path $InstallPath -File -Filter $pattern -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if ($candidate) {
            return $candidate
        }
    }
    return $null
}

function Invoke-ProcessWithTimeout(
    [string]$FilePath,
    [string[]]$ArgumentList,
    [int]$TimeoutSeconds,
    [string]$OperationName
) {
    $process = Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -PassThru
    $finishedInTime = $process.WaitForExit($TimeoutSeconds * 1000)
    if (-not $finishedInTime) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        throw "$OperationName timed out after $TimeoutSeconds seconds"
    }
    return [int]$process.ExitCode
}

function Invoke-PortableLaunchSmoke(
    [string]$ExecutablePath,
    [int]$TimeoutSeconds
) {
    $process = Start-Process -FilePath $ExecutablePath -ArgumentList @("--no-sandbox") -PassThru
    Start-Sleep -Seconds 2
    $started = -not $process.HasExited
    if (-not $started) {
        return [ordered]@{
            started = $false
            exit_code = [int]$process.ExitCode
            timed_out = $false
        }
    }

    $finishedInTime = $process.WaitForExit($TimeoutSeconds * 1000)
    if (-not $finishedInTime) {
        Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        return [ordered]@{
            started = $true
            exit_code = $null
            timed_out = $true
        }
    }

    return [ordered]@{
        started = $true
        exit_code = [int]$process.ExitCode
        timed_out = $false
    }
}

$installer = Find-LatestInstaller -RootPath $RepoRoot
if (-not $installer) {
    throw "Packaging smoke failed: installer artifact not found in $RepoRoot"
}

$portableExecutable = Join-Path $RepoRoot "frontend\dist\win-unpacked\DataLogicEngine Desktop.exe"
if (-not (Test-Path -LiteralPath $portableExecutable)) {
    throw "Packaging smoke failed: portable executable not found at $portableExecutable. Build installer first."
}

$report = [ordered]@{
    generated_at = [DateTime]::UtcNow.ToString("o")
    repo_root = $RepoRoot
    mode = $Mode
    installer = $installer.FullName
    installer_sha256 = (Get-FileHash -LiteralPath $installer.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    installer_signature_status = [string](Get-AuthenticodeSignature -FilePath $installer.FullName).Status
    portable_executable = $portableExecutable
    portable_launch_started = $false
    portable_launch_exit_code = $null
    portable_launch_timed_out = $false
    installer_mode = [ordered]@{
        install_path = ""
        install_exit_code = $null
        install_success = $false
        installed_executable = ""
        uninstaller = ""
        uninstall_exit_code = $null
        uninstall_success = $false
    }
}

$portableResult = Invoke-PortableLaunchSmoke -ExecutablePath $portableExecutable -TimeoutSeconds $LaunchTimeoutSeconds
$report.portable_launch_started = [bool]$portableResult.started
$report.portable_launch_exit_code = $portableResult.exit_code
$report.portable_launch_timed_out = [bool]$portableResult.timed_out

if (-not $report.portable_launch_started) {
    throw "Portable launch smoke failed: packaged desktop executable exited immediately."
}

if ($Mode -eq "installer") {
    $tempRoot = Join-Path $env:TEMP ("dle-packaging-smoke-" + [Guid]::NewGuid().ToString("N"))
    $installPath = Join-Path $tempRoot "install"
    New-Item -ItemType Directory -Path $installPath -Force | Out-Null
    $report.installer_mode.install_path = $installPath

    try {
        Write-Host "Running installer-mode smoke from: $($installer.FullName)" -ForegroundColor Cyan
        $installExitCode = Invoke-ProcessWithTimeout `
            -FilePath $installer.FullName `
            -ArgumentList @("/S", "/D=$installPath") `
            -TimeoutSeconds $InstallTimeoutSeconds `
            -OperationName "Silent installer"
        $report.installer_mode.install_exit_code = $installExitCode
        if ($installExitCode -ne 0) {
            throw "Silent installer exited with code $installExitCode"
        }

        $installedExecutable = Get-ChildItem -Path $installPath -File -Filter "*.exe" -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notmatch "^(Uninstall|unins)" } |
            Sort-Object Length -Descending |
            Select-Object -First 1
        if (-not $installedExecutable) {
            throw "Silent installer finished but no installed executable was found in $installPath"
        }

        $report.installer_mode.install_success = $true
        $report.installer_mode.installed_executable = $installedExecutable.FullName

        $uninstaller = Find-Uninstaller -InstallPath $installPath
        if (-not $uninstaller) {
            throw "Uninstaller executable not found in $installPath"
        }
        $report.installer_mode.uninstaller = $uninstaller.FullName

        if (-not $SkipUninstall) {
            $uninstallExitCode = Invoke-ProcessWithTimeout `
                -FilePath $uninstaller.FullName `
                -ArgumentList @("/S") `
                -TimeoutSeconds $UninstallTimeoutSeconds `
                -OperationName "Silent uninstaller"
            $report.installer_mode.uninstall_exit_code = $uninstallExitCode
            if ($uninstallExitCode -ne 0) {
                throw "Silent uninstaller exited with code $uninstallExitCode"
            }

            Start-Sleep -Seconds 2
            if (Test-Path -LiteralPath $installedExecutable.FullName) {
                throw "Installed executable still present after uninstall: $($installedExecutable.FullName)"
            }

            $report.installer_mode.uninstall_success = $true
        }
    }
    finally {
        if (Test-Path -LiteralPath $tempRoot) {
            Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

$reportPath = Join-Path $RepoRoot "reports\packaging_smoke_report.json"
New-Item -ItemType Directory -Path (Split-Path $reportPath) -Force | Out-Null
$report | ConvertTo-Json -Depth 8 | Set-Content -Path $reportPath -Encoding utf8

Write-Host "Packaging smoke checks passed." -ForegroundColor Green
Write-Host "Report: $reportPath" -ForegroundColor Gray
