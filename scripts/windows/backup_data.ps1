<#
.SYNOPSIS
    Nightly backup script for UKG Desktop data residency.
#>
param(
    [string]$BaseDir = "C:\ProgramData\DataLogicEngine",
    [string]$BackupDir = "C:\ProgramData\DataLogicEngine\backups",
    [string]$DbUser = "postgres",
    [string]$DbName = "ukg"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

try {
    $date = Get-Date -Format "yyyy-MM-dd_HHmm"
    $dailyDir = Join-Path $BackupDir $date

    Write-Host "--- UKG Desktop: Starting Nightly Backup ($date) ---" -ForegroundColor Gray

    # 1. Setup Directories
    if (-not (Test-Path $dailyDir)) {
        New-Item -Path $dailyDir -ItemType Directory -Force | Out-Null
    }

    # 2. Backup PostgreSQL
    Write-Host "Exporting Database..."
    $dbPath = Join-Path $dailyDir "database_dump.sql"
    try {
        # Assuming pg_dump is in path or standard location
        & "C:\Program Files\PostgreSQL\15\bin\pg_dump.exe" -U $DbUser $DbName > $dbPath
    }
    catch {
        Write-Warning "Database backup failed. Ensure PostgreSQL tools are in PATH."
    }

    # 2. Backup Encrypted Vault and Audit Logs
    Write-Host "Capturing Vault and Audit Files..."
    $vaultDir = Join-Path $BaseDir "vault"
    $auditDir = Join-Path $BaseDir "audit"
    $zipPath = Join-Path $dailyDir "files_snapshot.zip"

    Compress-Archive -Path $vaultDir, $auditDir -DestinationPath $zipPath -Update

    # 3. Retention Policy (Clean up backups older than 7 days)
    Write-Host "Cleaning up old backups..."
    Get-ChildItem -Path $BackupDir | Where-Object { $_.PSIsContainer -and $_.CreationTime -lt (Get-Date).AddDays(-7) } | Remove-Item -Recurse -Force

    Write-Host "Backup Complete: $dailyDir" -ForegroundColor Green
}
catch {
    Write-Error "UKG Backup Failed: $($_.Exception.Message)"
}
