<#
.SYNOPSIS
  Runs minimist's own upstream regression tests for CVE-2021-44906 (test/proto.js from v1.2.6)
  against the vulnerable v1.2.5 and the fixed v1.2.6.
.DESCRIPTION
  Expected: v1.2.5 FAILS the "constructor" cases (the incomplete __proto__-only guard),
  and v1.2.6 PASSES them all. This is the maintainers' regression suite, so it shows that the
  fix works without any exploit code. Requires `npm install` at the repo root (for tape)
  and `scripts\setup-targets.ps1`.
#>
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$suite = Join-Path $root 'targets\minimist-1.2.6\test\proto.js'
$env:NODE_PATH = Join-Path $root 'node_modules'

foreach ($v in '1.2.5', '1.2.6') {
    $dir = Join-Path $root "targets\minimist-$v"
    $copy = Join-Path $dir 'test\proto-regression-1.2.6.js'
    Copy-Item $suite $copy -Force
    Write-Host "`n===== minimist $v : upstream CVE-2021-44906 regression tests =====" -ForegroundColor Cyan
    Push-Location $dir
    $out = node $copy 2>&1
    Pop-Location
    $out | Where-Object { $_ -match '^(# |not ok|ok )' } | ForEach-Object {
        $color = if ($_ -match '^not ok|^# fail') { 'Red' } elseif ($_ -match '^ok|^# pass') { 'Green' } else { 'Gray' }
        Write-Host $_ -ForegroundColor $color
    }
}
