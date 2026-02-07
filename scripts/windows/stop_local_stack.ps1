[CmdletBinding()]
Param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$PidFile = Join-Path $RepoRoot "logs\local_stack.pids.json"

if (-not (Test-Path -LiteralPath $PidFile)) {
    Write-Host "No PID file found at $PidFile. Nothing to stop."
    exit 0
}

$record = Get-Content -LiteralPath $PidFile -Raw | ConvertFrom-Json
$targets = @(
    @{ Name = "frontend"; Pid = $record.frontend_pid },
    @{ Name = "backend"; Pid = $record.backend_pid }
)

foreach ($target in $targets) {
    $pidValue = 0
    if ($target.Pid) {
        $pidValue = [int]$target.Pid
    }
    if ($pidValue -le 0) {
        continue
    }

    $process = Get-Process -Id $pidValue -ErrorAction SilentlyContinue
    if ($process) {
        & taskkill.exe /PID $pidValue /T /F | Out-Null
        Write-Host ("Stopped {0} process (PID {1})." -f $target.Name, $pidValue)
    }
}

Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
Write-Host "Local stack stop complete."
