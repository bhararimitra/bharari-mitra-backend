# Start the crawler worker in a hidden background window (Windows PowerShell).
# Usage (from backend/):
#   .\scripts\start_crawler_worker.ps1

$ErrorActionPreference = "Stop"
$Backend = Split-Path -Parent $PSScriptRoot
Set-Location $Backend

# Prefer the project Python 3.12 install (PATH `python` may point elsewhere)
$candidates = @(
    "C:\Users\sidde\AppData\Local\Programs\Python\Python312\python.exe",
    (Join-Path $Backend ".venv\Scripts\python.exe")
)
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if ($pythonCmd) {
    $candidates += $pythonCmd.Source
}

$python = $null
foreach ($candidate in $candidates) {
    if ($candidate -and (Test-Path $candidate)) {
        $python = $candidate
        break
    }
}
if (-not $python) {
    throw "Python not found. Edit scripts/start_crawler_worker.ps1 with your python path."
}

$logDir = Join-Path $Backend "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$outLog = Join-Path $logDir "crawler_worker.out.log"
$errLog = Join-Path $logDir "crawler_worker.err.log"

$proc = Start-Process -FilePath $python `
    -ArgumentList "scripts\crawler_worker.py" `
    -WorkingDirectory $Backend `
    -RedirectStandardOutput $outLog `
    -RedirectStandardError $errLog `
    -WindowStyle Hidden `
    -PassThru

Write-Host "Crawler worker started in background."
Write-Host "  Python: $python"
Write-Host "  PID:  $($proc.Id)"
Write-Host "  Out:  $outLog"
Write-Host "  Err:  $errLog"
Write-Host "Stop with: Stop-Process -Id $($proc.Id)"
