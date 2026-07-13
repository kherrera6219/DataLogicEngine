[CmdletBinding()]
Param(
    [switch]$WithDataServices
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$PidFile = Join-Path $RepoRoot "logs\local_stack.pids.json"

if (Test-Path -LiteralPath $PidFile) {
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
}
else {
    Write-Host "No PID file found at $PidFile. No application processes to stop."
}

if ($WithDataServices) {
    $dockerPath = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerPath) {
        Push-Location $RepoRoot
        try {
            docker compose stop db redis neo4j minio | Out-Null
            Write-Host "Stopped local data services (db/redis/neo4j/minio)."
        }
        finally {
            Pop-Location
        }
    }
}

Write-Host "Local stack stop complete."
