Set-Location $PSScriptRoot

$port = 9090
if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*API_PORT\s*=\s*(\d+)\s*$') { $port = [int]$matches[1] }
    }
}

Write-Host "=== HH AI start ===" -ForegroundColor Cyan
Write-Host "Port: $port"
Write-Host ""

$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    $env:API_PORT = "$using:port"
    & .\venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port $using:port 2>&1
}

Start-Sleep -Seconds 5

& .\venv\Scripts\python.exe scripts\verify_backend.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Backend check failed." -ForegroundColor Red
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -Force -ErrorAction SilentlyContinue
    exit 1
}

Write-Host ""
Write-Host "Backend OK. Starting bot..." -ForegroundColor Green
Write-Host ""

try {
    & .\venv\Scripts\python.exe -m bot.main
} finally {
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -Force -ErrorAction SilentlyContinue
}
