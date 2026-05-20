Set-Location $PSScriptRoot

if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*BACKEND_URL\s*=\s*(.+)\s*$') {
            $env:BACKEND_URL = $matches[1].Trim().Trim('"').Trim("'")
        }
    }
}

$url = if ($env:BACKEND_URL) { "$($env:BACKEND_URL.TrimEnd('/'))/health" } else { "http://127.0.0.1:9090/health" }
Write-Host "Checking $url ..."

try {
    $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5
    Write-Host "OK ($($r.StatusCode)): $($r.Content)" -ForegroundColor Green
    exit 0
} catch {
    Write-Host "ERROR: backend is not available" -ForegroundColor Red
    Write-Host $_.Exception.Message
    Write-Host ""
    Write-Host "Run: .\run_backend.ps1"
    exit 1
}
