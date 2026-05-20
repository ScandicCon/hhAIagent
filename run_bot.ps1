Set-Location $PSScriptRoot

# Bypass system HTTP proxy for localhost
$env:NO_PROXY = "127.0.0.1,localhost"
$env:no_proxy = "127.0.0.1,localhost"

if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*BACKEND_URL\s*=\s*(.+)\s*$') {
            $env:BACKEND_URL = $matches[1].Trim().Trim('"').Trim("'")
        }
    }
}

Write-Host "BACKEND_URL = $env:BACKEND_URL" -ForegroundColor Cyan
Write-Host "Checking backend..." -ForegroundColor Cyan

& .\venv\Scripts\python.exe scripts\verify_backend.py
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Start backend first: .\run_backend.ps1" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Checking Telegram API..." -ForegroundColor Cyan
& .\venv\Scripts\python.exe scripts\check_telegram.py
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Telegram is blocked or unreachable. Use VPN or TELEGRAM_PROXY in .env" -ForegroundColor Red
    exit 1
}

Write-Host "Starting bot..." -ForegroundColor Green
& .\venv\Scripts\python.exe -m bot.main
