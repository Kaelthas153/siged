$ErrorActionPreference = 'Stop'
$proyectoSiged = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $proyectoSiged
if (-not (Test-Path '.runtime.json')) { throw 'En otro equipo sigue la instalación del README.md.' }
$configSiged = Get-Content '.runtime.json' -Raw | ConvertFrom-Json
New-Item -ItemType Directory -Force 'logs' | Out-Null
& "$($configSiged.pgbin)/pg_isready.exe" -h 127.0.0.1 -p $configSiged.port -q
if ($LASTEXITCODE -ne 0) {
    Start-Process -FilePath "$($configSiged.pgbin)/postgres.exe" -ArgumentList '-D', ('"' + $configSiged.pgdata + '"'), '-h', '127.0.0.1', '-p', $configSiged.port -WindowStyle Hidden -RedirectStandardError "$proyectoSiged/logs/postgres-error.log" -RedirectStandardOutput "$proyectoSiged/logs/postgres.log"
    for ($intentoSiged=0; $intentoSiged -lt 20; $intentoSiged++) {
        Start-Sleep -Milliseconds 500
        & "$($configSiged.pgbin)/pg_isready.exe" -h 127.0.0.1 -p $configSiged.port -q
        if ($LASTEXITCODE -eq 0) { break }
    }
    if ($LASTEXITCODE -ne 0) { throw 'No arrancó la base; revisa logs/postgres-error.log.' }
}
$puertoSiged = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if (-not $puertoSiged) {
    Start-Process -FilePath $configSiged.python -ArgumentList 'manage.py', 'runserver', '127.0.0.1:8000', '--noreload', '--insecure' -WorkingDirectory $proyectoSiged -WindowStyle Hidden -RedirectStandardOutput "$proyectoSiged/logs/web.log" -RedirectStandardError "$proyectoSiged/logs/web-error.log"
    Write-Host 'SIGED iniciado. Abre http://127.0.0.1:8000/ en unos segundos.'
} else { Write-Host 'El puerto 8000 ya está en uso. Si SIGED está abierto puedes continuar; si es otra aplicación, detenla o usa otro puerto según README.' }
Write-Host 'Consulta las cuentas en .demo-credentials.txt.'
