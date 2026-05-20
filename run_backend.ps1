Set-Location $PSScriptRoot

$env:NO_PROXY = "127.0.0.1,localhost"
$env:no_proxy = "127.0.0.1,localhost"

Write-Host "Picking free port..." -ForegroundColor Cyan
& .\venv\Scripts\python.exe scripts\pick_port.py
if ($LASTEXITCODE -ne 0) { exit 1 }

$port = 9090
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*API_PORT\s*=\s*(\d+)\s*$') { $port = [int]$matches[1] }
}

$url = "http://127.0.0.1:$port"
$env:API_PORT = "$port"

function Test-OurBackend {
    try {
        $root = Invoke-RestMethod -Uri "$url/" -TimeoutSec 2
        return ($root.app -eq "hh-ai-backend")
    } catch {
        return $false
    }
}

$listen = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($listen -and -not (Test-OurBackend)) {
    $procId = $listen.OwningProcess | Select-Object -First 1
    Write-Host "Port $port is used by PID $procId. Stopping it..." -ForegroundColor Yellow
    Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

if (Test-OurBackend) {
    Write-Host "Backend already running: $url" -ForegroundColor Green
    & .\venv\Scripts\python.exe scripts\verify_backend.py
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Starting backend: $url" -ForegroundColor Green
Write-Host "After start run: .\venv\Scripts\python.exe scripts\verify_backend.py"
Write-Host ""

& .\venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port $port
