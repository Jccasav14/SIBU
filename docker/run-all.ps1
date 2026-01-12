# Run all SIBU docker stacks (data first, then micros)
# From the repo root:  .\docker\run-all.ps1
$ErrorActionPreference = "Stop"

$base = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "==> Starting DATA stack..."
Push-Location (Join-Path $base "data")
docker compose up -d
Pop-Location

$services = @("auth","users","cases","appointments","notifications","audit_log","reports","admin","claims","coverage")

foreach ($s in $services) {
  Write-Host "==> Starting $s ..."
  Push-Location (Join-Path $base $s)
  docker compose up -d
  Pop-Location
}

Write-Host "DONE. Check: docker ps"
