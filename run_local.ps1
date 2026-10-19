$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
$manageFile = Join-Path $projectRoot 'manage.py'
$listenPort = if ($env:PHOTOTRACE_PORT) { $env:PHOTOTRACE_PORT } else { '8000' }
if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw 'Python environment not found. Run SETUP.cmd first.'
}
Push-Location $projectRoot
$worker = $null
try {
    & $pythonExe $manageFile migrate --noinput
    if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
    & $pythonExe $manageFile purge_expired
    if ($LASTEXITCODE -ne 0) { throw 'Expired-record cleanup failed.' }
    $worker = Start-Process -FilePath $pythonExe -ArgumentList ('"' + $manageFile + '" run_analysis_worker') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectRoot 'var\worker.out.log') -RedirectStandardError (Join-Path $projectRoot 'var\worker.err.log')
    Write-Host "PhotoTrace: http://127.0.0.1:$listenPort/"
    Write-Host 'Press Ctrl+C to stop.'
    & $pythonExe $manageFile runserver "127.0.0.1:$listenPort" --noreload
} finally {
    if ($worker -and -not $worker.HasExited) {
        Stop-Process -Id $worker.Id -ErrorAction SilentlyContinue
    }
    Pop-Location
}
