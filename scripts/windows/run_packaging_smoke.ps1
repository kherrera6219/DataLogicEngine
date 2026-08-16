[CmdletBinding()]
Param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path,
    [ValidateSet("portable", "installer")]
    [string]$Mode = "portable",
    [switch]$RequireBackendReady,
    [string]$BackendReadyUri = "http://127.0.0.1:5000/ready",
    [int]$BackendReadyTimeoutSeconds = 180,
    [int]$BackendReadyPollMilliseconds = 1000,
    [switch]$SkipUninstall,
    [int]$LaunchTimeoutSeconds = 25,
    [int]$InstallTimeoutSeconds = 240,
    [int]$UninstallTimeoutSeconds = 180,
    [int]$UninstallCleanupTimeoutSeconds = 120
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

function Wait-PathRemoved(
    [string]$Path,
    [int]$TimeoutSeconds,
    [string]$Description
) {
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (-not (Test-Path -LiteralPath $Path)) {
            return
        }
        Start-Sleep -Seconds 1
    }

    throw "$Description still present after waiting $TimeoutSeconds seconds: $Path"
}

function Invoke-PortableLaunchSmoke(
    [string]$ExecutablePath,
    [int]$TimeoutSeconds,
    [bool]$RequireReadiness,
    [uri]$ReadinessUri,
    [int]$ReadinessTimeoutSeconds,
    [int]$ReadinessPollMilliseconds
) {
    if ($RequireReadiness) {
        if ($ReadinessTimeoutSeconds -le 0) {
            throw "Backend readiness timeout must be greater than zero."
        }
        if ($ReadinessPollMilliseconds -lt 100) {
            throw "Backend readiness polling interval must be at least 100 milliseconds."
        }

        $existingListener = Get-NetTCPConnection `
            -LocalPort $ReadinessUri.Port `
            -State Listen `
            -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($existingListener) {
            throw "Backend readiness precondition failed: port $($ReadinessUri.Port) was already listening before the packaged application launched."
        }
    }

    $process = Start-Process -FilePath $ExecutablePath -ArgumentList @("--no-sandbox") -PassThru
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    Start-Sleep -Seconds 2
    $started = -not $process.HasExited
    if (-not $started) {
        return [ordered]@{
            started = $false
            exit_code = [int]$process.ExitCode
            timed_out = $false
            backend_ready = $false
            backend_ready_latency_ms = $null
            backend_ready_status = "process_exited"
            backend_ready_blockers = @()
            backend_ready_owner_pid = $null
            backend_ready_owner_verified = $false
            backend_ready_error = "Packaged desktop executable exited before readiness could be evaluated."
        }
    }

    $result = [ordered]@{
        started = $true
        exit_code = $null
        timed_out = $false
        backend_ready = $false
        backend_ready_latency_ms = $null
        backend_ready_status = if ($RequireReadiness) { "not_ready" } else { "not_required" }
        backend_ready_blockers = @()
        backend_ready_owner_pid = $null
        backend_ready_owner_verified = $false
        backend_ready_error = ""
    }

    try {
        if (-not $RequireReadiness) {
            $finishedInTime = $process.WaitForExit($TimeoutSeconds * 1000)
            if ($finishedInTime) {
                $result.exit_code = [int]$process.ExitCode
            }
            else {
                $result.timed_out = $true
            }
            return $result
        }

        $deadline = [DateTime]::UtcNow.AddSeconds($ReadinessTimeoutSeconds)
        while ([DateTime]::UtcNow -lt $deadline) {
            if ($process.HasExited) {
                $result.exit_code = [int]$process.ExitCode
                $result.backend_ready_status = "process_exited"
                $result.backend_ready_error = "Packaged desktop executable exited before the backend reported ready."
                return $result
            }

            try {
                $response = Invoke-RestMethod `
                    -Uri $ReadinessUri.AbsoluteUri `
                    -Method Get `
                    -TimeoutSec 5
                $blockers = @($response.blockers)
                $result.backend_ready_status = [string]$response.status
                $result.backend_ready_blockers = $blockers

                if ($response.status -eq "ready" -and $blockers.Count -eq 0) {
                    $listener = Get-NetTCPConnection `
                        -LocalPort $ReadinessUri.Port `
                        -State Listen `
                        -ErrorAction SilentlyContinue |
                        Select-Object -First 1
                    if (-not $listener) {
                        $result.backend_ready_error = "The readiness endpoint responded, but no listener owner could be resolved."
                    }
                    else {
                        $result.backend_ready_owner_pid = [int]$listener.OwningProcess
                        $candidatePid = [int]$listener.OwningProcess
                        $seen = [System.Collections.Generic.HashSet[int]]::new()
                        while ($candidatePid -gt 0 -and $seen.Add($candidatePid)) {
                            if ($candidatePid -eq $process.Id) {
                                $result.backend_ready_owner_verified = $true
                                break
                            }
                            $candidate = Get-CimInstance `
                                -ClassName Win32_Process `
                                -Filter "ProcessId = $candidatePid" `
                                -ErrorAction SilentlyContinue
                            if (-not $candidate) {
                                break
                            }
                            $candidatePid = [int]$candidate.ParentProcessId
                        }

                        if ($result.backend_ready_owner_verified) {
                            $result.backend_ready = $true
                            $result.backend_ready_latency_ms = [int64]$stopwatch.ElapsedMilliseconds
                            $result.backend_ready_error = ""
                            return $result
                        }
                        $result.backend_ready_error = "Port $($ReadinessUri.Port) is owned by a process outside the launched package process tree."
                    }
                }
            }
            catch {
                $result.backend_ready_error = $_.Exception.Message
            }

            Start-Sleep -Milliseconds $ReadinessPollMilliseconds
        }

        $result.timed_out = $true
        if (-not $result.backend_ready_error) {
            $result.backend_ready_error = "Backend did not report ready within $ReadinessTimeoutSeconds seconds."
        }
        return $result
    }
    finally {
        if (-not $process.HasExited) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
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

$sourceCommit = "unknown"
try {
    $resolvedCommit = (& git -C $RepoRoot rev-parse HEAD 2>$null)
    if ($LASTEXITCODE -eq 0 -and $resolvedCommit) {
        $sourceCommit = ([string]$resolvedCommit).Trim()
    }
} catch {
    # Preserve smoke execution when Git metadata is unavailable in a release workspace.
}

$report = [ordered]@{
    status = "pending"
    failure_reason = ""
    generated_at = [DateTime]::UtcNow.ToString("o")
    repo_root = $RepoRoot
    source_commit = $sourceCommit
    mode = $Mode
    installer = $installer.FullName
    installer_sha256 = (Get-FileHash -LiteralPath $installer.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    installer_signature_status = [string](Get-AuthenticodeSignature -FilePath $installer.FullName).Status
    portable_executable = $portableExecutable
    portable_launch_started = $false
    portable_launch_exit_code = $null
    portable_launch_timed_out = $false
    backend_readiness = [ordered]@{
        required = [bool]$RequireBackendReady
        uri = $BackendReadyUri
        ready = $false
        latency_ms = $null
        status = if ($RequireBackendReady) { "not_evaluated" } else { "not_required" }
        blockers = @()
        owner_pid = $null
        owner_verified_as_launch_descendant = $false
        error = ""
    }
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

$portableResult = Invoke-PortableLaunchSmoke `
    -ExecutablePath $portableExecutable `
    -TimeoutSeconds $LaunchTimeoutSeconds `
    -RequireReadiness ([bool]$RequireBackendReady) `
    -ReadinessUri ([uri]$BackendReadyUri) `
    -ReadinessTimeoutSeconds $BackendReadyTimeoutSeconds `
    -ReadinessPollMilliseconds $BackendReadyPollMilliseconds
$report.portable_launch_started = [bool]$portableResult.started
$report.portable_launch_exit_code = $portableResult.exit_code
$report.portable_launch_timed_out = [bool]$portableResult.timed_out
$report.backend_readiness.ready = [bool]$portableResult.backend_ready
$report.backend_readiness.latency_ms = $portableResult.backend_ready_latency_ms
$report.backend_readiness.status = [string]$portableResult.backend_ready_status
$report.backend_readiness.blockers = @($portableResult.backend_ready_blockers)
$report.backend_readiness.owner_pid = $portableResult.backend_ready_owner_pid
$report.backend_readiness.owner_verified_as_launch_descendant = [bool]$portableResult.backend_ready_owner_verified
$report.backend_readiness.error = [string]$portableResult.backend_ready_error

if (-not $report.portable_launch_started) {
    $report.failure_reason = "Portable launch smoke failed: packaged desktop executable exited immediately."
}
elseif ($RequireBackendReady -and -not $report.backend_readiness.ready) {
    $report.failure_reason = "Portable readiness smoke failed: $($report.backend_readiness.error)"
}

if (-not $report.failure_reason -and $Mode -eq "installer") {
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

            Wait-PathRemoved `
                -Path $installedExecutable.FullName `
                -TimeoutSeconds $UninstallCleanupTimeoutSeconds `
                -Description "Installed executable"

            $report.installer_mode.uninstall_success = $true
        }
    }
    finally {
        if (Test-Path -LiteralPath $tempRoot) {
            try {
                Remove-Item -LiteralPath $tempRoot -Recurse -Force
            } catch {
                # Ignore folder cleanup errors
            }
        }
    }
}

$report.status = if ($report.failure_reason) { "fail" } else { "pass" }
$reportPath = Join-Path $RepoRoot "reports\packaging_smoke_report.json"
New-Item -ItemType Directory -Path (Split-Path $reportPath) -Force | Out-Null
$report | ConvertTo-Json -Depth 8 | Set-Content -Path $reportPath -Encoding utf8

if ($report.failure_reason) {
    throw $report.failure_reason
}

Write-Host "Packaging smoke checks passed." -ForegroundColor Green
Write-Host "Report: $reportPath" -ForegroundColor Gray
