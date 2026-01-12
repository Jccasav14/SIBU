# Stop everything and wipe volumes (clean reset)
# From the repo root:  .\docker\down-all.ps1
$ErrorActionPreference = "Continue"
$base = Split-Path -Parent $MyInvocation.MyCommand.Path

$services = @("coverage","claims","admin","reports","audit_log","notifications","appointments","cases","users","auth","data")
foreach ($s in $services) {
  $p = Join-Path $base $s
  if (Test-Path $p) {
    Push-Location $p
    docker compose down -v
    Pop-Location
  }
}

docker system prune -af
docker volume prune -f
docker network prune -f
Write-Host "DONE."
