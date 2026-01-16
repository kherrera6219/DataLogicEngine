<#
.SYNOPSIS
    Installs Redis (Memurai) silently for DataLogicEngine.
#>
param(
    [string]$Port = "6379"
)

$ErrorActionPreference = "Stop"

Write-Host "--- UKG Desktop: Setting up Redis Cache ---" -ForegroundColor Cyan

# Check for existing installation (Redis or Memurai)
if (Get-Service "redis" -ErrorAction SilentlyContinue -or Get-Service "memurai" -ErrorAction SilentlyContinue) {
    Write-Host "Redis/Memurai already installed." -ForegroundColor Yellow
    return
}

# Download Memurai (Windows-native Redis)
$msiPath = Join-Path $env:TEMP "Memurai-Developer.msi"
if (-not (Test-Path $msiPath)) {
    Write-Host "Downloading Memurai Developer Edition..."
    $url = "https://www.memurai.com/get-memurai/latest/developer"
    Invoke-WebRequest -Uri $url -OutFile $msiPath
}

# Start Silent Installation
Write-Host "Running silent MSI installation..."
Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$msiPath`" /qn /norestart" -Wait -NoNewWindow

# Verify
Start-Sleep -Seconds 5
if (Get-Service "memurai" -ErrorAction SilentlyContinue) {
    Write-Host "Redis service (Memurai) installed successfully." -ForegroundColor Green
} else {
    Write-Warning "Memurai service not found. Attempting to start if installed..."
}
