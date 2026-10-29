$ErrorActionPreference = 'Stop'
$proyectoSiged = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $proyectoSiged
$configSiged = Get-Content '.runtime.json' -Raw | ConvertFrom-Json
$usuarioPrevioSiged=$env:DB_USER
$clavePreviaSiged=$env:DB_PASSWORD
$basePruebasPreviaSiged=$env:DB_TEST_NAME
try {
    $env:DB_USER='siged_owner'
    $env:DB_PASSWORD=[System.IO.File]::ReadAllText($configSiged.owner_password_file).Trim()
    $env:DB_TEST_NAME='test_siged_semana2'
    & $configSiged.python manage.py test incidents --verbosity 2 --keepdb --noinput
    if ($LASTEXITCODE -ne 0) { throw 'Las pruebas detectaron errores.' }
} finally { $env:DB_USER=$usuarioPrevioSiged; $env:DB_PASSWORD=$clavePreviaSiged; $env:DB_TEST_NAME=$basePruebasPreviaSiged }
