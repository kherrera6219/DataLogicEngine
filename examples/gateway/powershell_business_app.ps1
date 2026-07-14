$baseUrl = if ($env:DATALOGICENGINE_API_URL) { $env:DATALOGICENGINE_API_URL } else { "http://127.0.0.1:5000/api/v1" }
$clientKey = $env:DATALOGICENGINE_API_KEY
if (-not $clientKey) { throw "Set DATALOGICENGINE_API_KEY to a copy-once DataLogicEngine client key." }

$body = @{
    virtual_model = "dle-standard"
    request_id = [guid]::NewGuid().ToString()
    idempotency_key = [guid]::NewGuid().ToString()
    messages = @(@{ role = "user"; content = "Summarize the approved evidence." })
} | ConvertTo-Json -Depth 8

Invoke-RestMethod -Method Post -Uri "$baseUrl/gateway/chat" `
    -Headers @{ Authorization = "Bearer $clientKey" } `
    -ContentType "application/json" -Body $body
