param(
    [string]$Port = "6379"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ServiceName = "UKG-Redis"
$ExpectedMsiHash = "F2A3F2A3F2A3F2A3F2A3F2A3F2A3F2A3F2A3F2A3F2A3F2A3F2A3F2A3F2A3F2A3" # Placeholder
$MsiPath = Join-Path $env:TEMP "Memurai-Developer.msi"

try {
    Write-Host "--- UKG Desktop: Setting up Redis Cache ($ServiceName) ---" -ForegroundColor Cyan

    # Integrity Check
    if (Get-Command Test-UKGFileHash -ErrorAction SilentlyContinue) {
        if (Test-Path $MsiPath) {
            Test-UKGFileHash -Path $MsiPath -ExpectedHash $ExpectedMsiHash
        }
    }

    # Check for existing installation
    if (Get-Service $ServiceName -ErrorAction SilentlyContinue) {
        Write-Host "Redis ($ServiceName) already installed." -ForegroundColor Yellow
        return
    }

    # Download Memurai (Windows-native Redis)
    if (-not (Test-Path $MsiPath)) {
        Write-Host "Downloading Memurai Developer Edition..."
        $url = "https://www.memurai.com/get-memurai/latest/developer"
        Invoke-WebRequest -Uri $url -OutFile $MsiPath
    }

    # Start Silent Installation
    Write-Host "Running silent MSI installation..."
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$MsiPath`" /qn /norestart" -Wait -NoNewWindow

    # Post-install: Rename service to UKG-Redis if needed
    # Default Memurai service name is 'Memurai'
    if (Get-Service "memurai" -ErrorAction SilentlyContinue) {
        Write-Host "Standardizing Redis service name to $ServiceName..."
        Stop-Service "memurai" -ErrorAction SilentlyContinue
        # We use sc.exe to rename/re-register if necessary, or just track 'memurai'
        # For simplicity in this blueprint, we'll try to rename via sc config
        & sc.exe config memurai displayname= "$ServiceName" | Out-Null
    }

    # Verify
    Start-Sleep -Seconds 2
    if (Get-Service "memurai" -ErrorAction SilentlyContinue) {
        Write-Host "Redis service installed successfully." -ForegroundColor Green
    }
    else {
        throw "Redis installation failed: Service not found after execution."
    }
}
catch {
    Write-Host "Redis Setup Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
