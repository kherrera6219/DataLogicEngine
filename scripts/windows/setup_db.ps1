param(
    [Parameter(Mandatory = $false)]
    [String]$InstallDir = "C:\Program Files\PostgreSQL\15",

    [Parameter(Mandatory = $false)]
    [String]$DataDir = "C:\ProgramData\DataLogicEngine\db",

    [Parameter(Mandatory = $false)]
    [SecureString]$Password,

    [Parameter(Mandatory = $false)]
    [String]$Database = "ukg_local",

    [Parameter(Mandatory = $false)]
    [String]$DbUser = "ukg_app"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Convert password to plain text for PostgreSQL (it requires PGPASSWORD env var)
if (-not $Password) {
    $Password = ConvertTo-SecureString -String "ukg_local_pwd" -AsPlainText -Force
}
$PlainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($Password)
)

$ServiceName = "UKG-Postgres"
$ExpectedMsiHash = "815C815C815C815C815C815C815C815C815C815C815C815C815C815C815C815C" # Placeholder
$MsiPath = Join-Path $env:TEMP "postgresql-15-windows-x64.exe"

try {
    Write-Host "--- UKG Desktop: Setting up PostgreSQL ($ServiceName) ---" -ForegroundColor Cyan

    # 1. Pre-flight: Port Check
    $Port = 5432
    $Connection = New-Object System.Net.Sockets.TcpClient
    $PortOccupied = $false
    try {
        $Connection.Connect("127.0.0.1", $Port)
        $PortOccupied = $true
        $Connection.Close()
    }
    catch {
        # Port is free
    }

    if ($PortOccupied) {
        throw "Port $Port is already occupied. Cannot install PostgreSQL."
    }

    # 2. Integrity Check
    if (Get-Command Test-UKGFileHash -ErrorAction SilentlyContinue) {
        if (Test-Path $MsiPath) {
            Test-UKGFileHash -Path $MsiPath -ExpectedHash $ExpectedMsiHash
        }
    }

    # 3. Check for existing installation
    if (Get-Service $ServiceName -ErrorAction SilentlyContinue) {
        Write-Host "PostgreSQL ($ServiceName) already installed." -ForegroundColor Yellow
        return
    }

    # 4. Download MSI if missing
    if (-not (Test-Path $MsiPath)) {
        Write-Host "Downloading PostgreSQL installer..."
        $url = "https://get.enterprisedb.com/postgresql/postgresql-15.5-1-windows-x64.exe"
        Invoke-WebRequest -Uri $url -OutFile $MsiPath
    }

    # 5. Start Silent Installation
    Write-Host "Running silent installation... this may take a few minutes."
    # Note: --servicename is the EDB flag for custom service names
    $arguments = "--mode unattended --unattendedmodeui none --install_runtimes 1 --enable_stackbuilder 0 --password $Password --datadir `"$DataDir`" --installdir `"$InstallDir`" --servicename $ServiceName"
    Start-Process -FilePath $MsiPath -ArgumentList $arguments -Wait -NoNewWindow

    # 6. Verify service
    if (-not (Get-Service $ServiceName -ErrorAction SilentlyContinue)) {
        throw "PostgreSQL installation failed: Service $ServiceName not found."
    }

    # 7. Lockdown: Bind to localhost (pg_hba.conf hardening)
    $HbaPath = Join-Path $DataDir "pg_hba.conf"
    if (Test-Path $HbaPath) {
        Write-Host "Applying pg_hba.conf hardening..."
        $HbaContent = @(
            "# UKG Hardened Access Control",
            "host    all             all             127.0.0.1/32            scram-sha-256",
            "host    all             all             ::1/128                 scram-sha-256",
            "local   all             all                                     scram-sha-256"
        )
        $HbaContent | Out-File $HbaPath -Encoding ASCII -Force
        Restart-Service $ServiceName
    }

    # 8. Create Application DB and User
    Write-Host "Initializing $Database and $DbUser..."
    $env:PGPASSWORD = $PlainPassword
    $Psql = Join-Path $InstallDir "bin\psql.exe"
    
    # Create Role
    & $Psql -U postgres -c "CREATE ROLE $DbUser WITH LOGIN PASSWORD '$PlainPassword';" -h localhost 2>$null
    # Create DB
    & $Psql -U postgres -c "CREATE DATABASE $Database OWNER $DbUser;" -h localhost 2>$null
    
    Write-Host "PostgreSQL setup complete." -ForegroundColor Green
}
catch {
    Write-Host "PostgreSQL Setup Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
finally {
    $env:PGPASSWORD = $null
}
