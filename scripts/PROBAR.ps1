$ErrorActionPreference = 'Stop'
$proyectoSiged = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $proyectoSiged
$configSiged = Get-Content '.runtime.json' -Raw | ConvertFrom-Json
$usuarioPrevioSiged=$env:DB_USER
$clavePreviaSiged=$env:DB_PASSWORD
try {
    $env:DB_USER='siged_owner'
    $env:DB_PASSWORD=[System.IO.File]::ReadAllText($configSiged.owner_password_file).Trim()
    & $configSiged.python manage.py test incidents --verbosity 2
    if ($LASTEXITCODE -ne 0) { throw 'Las pruebas detectaron errores.' }
} finally { $env:DB_USER=$usuarioPrevioSiged; $env:DB_PASSWORD=$clavePreviaSiged }
