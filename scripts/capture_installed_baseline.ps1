[CmdletBinding()]
param(
    [string]$OutputPath = "reports/production-readiness/2026/phase-00/runtime/installed-baseline.json"
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$resolvedOutput = if ([IO.Path]::IsPathRooted($OutputPath)) { $OutputPath } else { Join-Path $root $OutputPath }

function Get-CommandVersion {
    param([string]$Name, [string[]]$Arguments = @("--version"))
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        return [ordered]@{ available = $false; path = $null; version = $null }
    }
    $commandPath = $command.Source
    $version = $null
    try {
        $version = ((& $commandPath @Arguments 2>&1) | Select-Object -First 1 | Out-String).Replace(([string][char]0), "").Trim()
    } catch {
        $version = "version-query-failed"
    }
    return [ordered]@{ available = $true; path = $commandPath; version = $version }
}

function Invoke-RedactedCommand {
    param([string]$Executable, [string[]]$Arguments)
    $command = Get-Command $Executable -ErrorAction SilentlyContinue
    if (-not $command) { return $null }
    $commandPath = $command.Source
    $previousPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = "Continue"
        return ((& $commandPath @Arguments 2>&1) | Out-String).Replace(([string][char]0), "").Trim()
    } catch {
        return "command-failed"
    } finally {
        $ErrorActionPreference = $previousPreference
    }
}

$os = Get-CimInstance Win32_OperatingSystem
$computer = Get-CimInstance Win32_ComputerSystem
$systemDrive = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$($os.SystemDrive)'"
$gitStatus = Invoke-RedactedCommand -Executable "git" -Arguments @("status", "--porcelain")
$composeServicesRaw = Invoke-RedactedCommand -Executable "docker" -Arguments @("compose", "-f", (Join-Path $root "docker-compose.yml"), "config", "--services")
$composeServices = if ($composeServicesRaw) {
    @(
        $composeServicesRaw -split "`r?`n" |
            ForEach-Object { $_.Trim() } |
            Where-Object { $_ -match "^[a-z0-9][a-z0-9_-]*$" }
    )
} else { @() }
$dockerInfo = Invoke-RedactedCommand -Executable "docker" -Arguments @("version", "--format", "{{json .}}")
$podmanInfo = Invoke-RedactedCommand -Executable "podman" -Arguments @("version", "--format", "json")
$podmanMachines = Invoke-RedactedCommand -Executable "podman" -Arguments @("machine", "list", "--format", "json")
$wslStatus = Invoke-RedactedCommand -Executable "wsl" -Arguments @("--status")
$installerPath = Join-Path $root "DataLogicEngine Setup Latest.exe"

$installer = [ordered]@{ exists = $false; path = "DataLogicEngine Setup Latest.exe"; size = $null; sha256 = $null; signature = $null }
if (Test-Path -LiteralPath $installerPath) {
    $item = Get-Item -LiteralPath $installerPath
    $signature = Get-AuthenticodeSignature -LiteralPath $installerPath
    $installer = [ordered]@{
        exists = $true
        path = "DataLogicEngine Setup Latest.exe"
        size = $item.Length
        sha256 = (Get-FileHash -LiteralPath $installerPath -Algorithm SHA256).Hash.ToLowerInvariant()
        signature = $signature.Status.ToString()
    }
}

$payload = [ordered]@{
    schema_version = "1.0.0"
    captured_at = [DateTimeOffset]::UtcNow.ToString("o")
    authority = "PRODUCTION_COMPLETION_PLAN_2026.md v1.2.0"
    host = [ordered]@{
        os_caption = $os.Caption
        os_version = $os.Version
        os_build = $os.BuildNumber
        architecture = $os.OSArchitecture
        manufacturer = $computer.Manufacturer
        model = $computer.Model
        total_memory_bytes = [int64]$computer.TotalPhysicalMemory
        system_drive_free_bytes = [int64]$systemDrive.FreeSpace
        system_drive_size_bytes = [int64]$systemDrive.Size
    }
    toolchain = [ordered]@{
        python = Get-CommandVersion -Name "python"
        node = Get-CommandVersion -Name "node"
        npm = Get-CommandVersion -Name "npm"
        docker = Get-CommandVersion -Name "docker"
        podman = Get-CommandVersion -Name "podman"
        wsl = Get-CommandVersion -Name "wsl" -Arguments @("--version")
    }
    container_runtime = [ordered]@{
        production_reference = "podman-machine-wsl2"
        reference_available = [bool](Get-Command podman -ErrorAction SilentlyContinue)
        podman_version = $podmanInfo
        podman_machines = $podmanMachines
        developer_docker_available = [bool](Get-Command docker -ErrorAction SilentlyContinue)
        docker_version = $dockerInfo
        wsl_status = $wslStatus
        compose_services = $composeServices
    }
    installer = $installer
    git = [ordered]@{
        head = Invoke-RedactedCommand -Executable "git" -Arguments @("rev-parse", "HEAD")
        branch = Invoke-RedactedCommand -Executable "git" -Arguments @("branch", "--show-current")
        working_tree_change_count = if ($gitStatus) { @($gitStatus -split "`r?`n").Count } else { 0 }
    }
    baseline_status = "captured-current-host-not-production-qualified"
    blockers = @(
        if (-not (Get-Command podman -ErrorAction SilentlyContinue)) {
            "Podman production reference runtime is not installed on this host."
        }
        "Current Compose profile omits required ChromaDB."
        "Current service image references are not immutable digests."
        "The existing unsigned 0.1.1 installer did not register a silent installed application."
    )
}

$outputDirectory = Split-Path -Parent $resolvedOutput
New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
$payload | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $resolvedOutput -Encoding utf8
Write-Output "Wrote $resolvedOutput"
