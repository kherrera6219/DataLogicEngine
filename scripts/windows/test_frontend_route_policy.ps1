[CmdletBinding()]
Param(
    [int]$FrontendPort = 3000,
    [string]$BaseUrl = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $BaseUrl) {
    $BaseUrl = "http://127.0.0.1:$FrontendPort"
}
$BaseUrl = $BaseUrl.TrimEnd("/")

function Write-Step([string]$Message, [string]$Color = "Cyan") {
    Write-Host $Message -ForegroundColor $Color
}

function Invoke-RouteStatus([string]$Url, [hashtable]$Headers = @{}, [int]$Attempts = 3) {
    for ($i = 1; $i -le $Attempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -MaximumRedirection 0 -TimeoutSec 20 -Headers $Headers -ErrorAction Stop
            return @{
                StatusCode = [int]$response.StatusCode
                Location = [string]$response.Headers["Location"]
            }
        }
        catch {
            if ($_.Exception.Response) {
                $response = $_.Exception.Response
                $location = ""
                try {
                    $location = [string]$response.Headers["Location"]
                }
                catch {
                    $location = ""
                }
                return @{
                    StatusCode = [int]$response.StatusCode
                    Location = $location
                }
            }

            if ($i -eq $Attempts) {
                throw "Request failed for $Url after $Attempts attempts. $($_.Exception.Message)"
            }
            Start-Sleep -Seconds 1
        }
    }
}

Write-Step "Running frontend route policy smoke checks against $BaseUrl ..."

$publicRoutes = @(
    "/",
    "/about",
    "/about/cloud-services",
    "/legal/privacy",
    "/login",
    "/register"
)

$protectedRoutes = @(
    "/dashboard",
    "/chat",
    "/projects",
    "/settings",
    "/projects/1"
)

$failures = New-Object System.Collections.Generic.List[string]

foreach ($route in $publicRoutes) {
    $result = Invoke-RouteStatus -Url "$BaseUrl$route"
    if ($result.StatusCode -ne 200) {
        $failures.Add("Public route '$route' expected 200 but received $($result.StatusCode).")
    }
}

foreach ($route in $protectedRoutes) {
    $result = Invoke-RouteStatus -Url "$BaseUrl$route"
    if ($result.StatusCode -ne 307) {
        $failures.Add("Protected route '$route' expected 307 redirect but received $($result.StatusCode).")
        continue
    }

    if ($result.Location -notmatch "/login\?callbackUrl=") {
        $failures.Add("Protected route '$route' redirect location did not include callbackUrl. Location='$($result.Location)'.")
    }
}

$desktopHeaders = @{ "x-datalogic-desktop" = "1" }
foreach ($route in $protectedRoutes) {
    $result = Invoke-RouteStatus -Url "$BaseUrl$route" -Headers $desktopHeaders
    if ($result.StatusCode -ne 200) {
        $failures.Add("Desktop bypass route '$route' expected 200 but received $($result.StatusCode).")
    }
}

if ($failures.Count -gt 0) {
    Write-Host ""
    Write-Step "Frontend route policy smoke checks failed:" "Red"
    foreach ($failure in $failures) {
        Write-Host " - $failure" -ForegroundColor Red
    }
    throw "Frontend route policy smoke checks reported $($failures.Count) failure(s)."
}

Write-Step "Frontend route policy smoke checks passed." "Green"
