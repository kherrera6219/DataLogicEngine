<#
.SYNOPSIS
    Installs PostgreSQL silently for DataLogicEngine.
#>
param(
    [string]$InstallDir = "C:\Program Files\PostgreSQL\15",
    [string]$DataDir = "C:\ProgramData\DataLogicEngine\db",
    [string]$Password = "ukg_local_pwd"
)

$ErrorActionPreference = "Stop"

Write-Host "--- UKG Desktop: Setting up PostgreSQL ---" -ForegroundColor Cyan

# Check for existing installation
if (Get-Service "postgresql-x64-15" -ErrorAction SilentlyContinue) {
    Write-Host "PostgreSQL already installed and registered." -ForegroundColor Yellow
    return
}

# Download MSI if not present (simulating bundling logic)
$msiPath = Join-Path $env:TEMP "postgresql-15-windows-x64.exe"
if (-not (Test-Path $msiPath)) {
    Write-Host "Downloading PostgreSQL installer..."
    # Note: In a real bundle, this would be local. Using public mirror for demonstration.
    $url = "https://get.enterprisedb.com/postgresql/postgresql-15.5-1-windows-x64.exe"
    Invoke-WebRequest -Uri $url -OutFile $msiPath
}

# Start Silent Installation
Write-Host "Running silent installation... this may take a few minutes."
$arguments = "--mode unattended --unattendedmodeui none --install_runtimes 1 --enable_stackbuilder 0 --password $Password --datadir `"$DataDir`" --installdir `"$InstallDir`""
Start-Process -FilePath $msiPath -ArgumentList $arguments -Wait -NoNewWindow

# Verify service
if (Get-Service "postgresql-x64-15" -ErrorAction SilentlyContinue) {
    Write-Host "PostgreSQL installed successfully." -ForegroundColor Green
} else {
    Write-Error "PostgreSQL installation failed."
}
