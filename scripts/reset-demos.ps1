<#
.SYNOPSIS
  Resets demo scratch state so the demos can be run again (rehearsal → real lecture).
  - Recreates the refactoring scratch copy at %TEMP%\legacy-invoice (a fresh git repo with a baseline commit)
  - Empties demo-output\ (where Copilot writes diagrams during Demo 2)
#>
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot

$scratch = Join-Path $env:TEMP 'legacy-invoice'
if (Test-Path $scratch) { Remove-Item -Recurse -Force $scratch }
Copy-Item -Recurse (Join-Path $root 'labs\legacy-invoice') $scratch
Get-ChildItem $scratch -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
Push-Location $scratch
git init -q -b main
git add -A
git -c user.name=demo -c user.email=demo@example.com commit -q -m 'baseline'
Pop-Location
Write-Host "Refactoring scratch repo ready: $scratch"

$out = Join-Path $root 'demo-output'
if (Test-Path $out) { Remove-Item -Recurse -Force $out }
New-Item -ItemType Directory $out | Out-Null
Write-Host "Empty diagram folder ready:   $out"
