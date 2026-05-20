# Local Docker deploy test
Set-Location $PSScriptRoot

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Created .env from .env.example - fill in secrets!" -ForegroundColor Yellow
    exit 1
}

docker compose up -d --build
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host ""
Write-Host "API:  http://127.0.0.1:9090/welcome" -ForegroundColor Green
Write-Host "Health: http://127.0.0.1:9090/health" -ForegroundColor Green
Write-Host "Logs: docker compose logs -f" -ForegroundColor Cyan
