# Starts uvicorn + Cloudflare tunnel for api.sinehan.dev

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Activate venv
$venvActivate = Join-Path $ScriptDir "venv\Scripts\Activate.ps1"
if (Test-Path $venvActivate) {
    Write-Host "Activating venv..."
    & $venvActivate
} else {
    Write-Host "Warning: venv not found at $venvActivate, proceeding without it..."
}

# Start Qdrant Docker container
$qdrantRunning = docker ps --filter "name=qdrant" --format "{{.Names}}" 2>$null
if ($qdrantRunning -eq "qdrant") {
    Write-Host "Qdrant already running."
} else {
    $qdrantExists = docker ps -a --filter "name=qdrant" --format "{{.Names}}" 2>$null
    if ($qdrantExists -eq "qdrant") {
        Write-Host "Starting existing Qdrant container..."
        docker start qdrant
    } else {
        Write-Host "Creating and starting Qdrant container..."
        docker run -d --name qdrant -p 6333:6333 -v "$ScriptDir/qdrant_storage:/qdrant/storage" qdrant/qdrant
    }
    Start-Sleep -Seconds 2
}

Write-Host "Starting uvicorn on :8000..."
$uvicorn = Start-Process -NoNewWindow -PassThru -FilePath "python" -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8000"

Start-Sleep -Seconds 2

Write-Host "Starting Cloudflare tunnel..."
$tunnel = Start-Process -NoNewWindow -PassThru -FilePath "cloudflared" -ArgumentList "tunnel --config $ScriptDir\.cloudflared\config.yml run api"

Write-Host "Running - uvicorn (PID $($uvicorn.Id)) + tunnel (PID $($tunnel.Id))"
Write-Host "Press Ctrl+C to stop."

try {
    Wait-Process -Id $uvicorn.Id, $tunnel.Id
} finally {
    Write-Host "Shutting down..."
    Stop-Process -Id $uvicorn.Id -ErrorAction SilentlyContinue
    Stop-Process -Id $tunnel.Id -ErrorAction SilentlyContinue
}
