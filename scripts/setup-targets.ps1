<#
.SYNOPSIS
  Clones the pinned open-source "analysis targets" used in the lecture demos into .\targets.
.DESCRIPTION
  Versions are pinned so prompts and expected findings stay reproducible.
  Some targets are intentionally OLD, VULNERABLE versions used only for defensive study
  (find the bug, then compare with the upstream fix). Never deploy them.
.EXAMPLE
  .\scripts\setup-targets.ps1                  # clone everything
  .\scripts\setup-targets.ps1 -Only tinydb,minimist
#>
param([string[]]$Only)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$targetsDir = Join-Path $root 'targets'
New-Item -ItemType Directory -Force -Path $targetsDir | Out-Null

$targets = @(
    @{ name = 'tinydb';          url = 'https://github.com/msiemens/tinydb.git';     tag = 'v4.8.0'  }  # Demo 1: understanding
    @{ name = 'flask';           url = 'https://github.com/pallets/flask.git';       tag = '3.0.3'   }  # Demo 2: architecture (Python)
    @{ name = 'express';         url = 'https://github.com/expressjs/express.git';   tag = '4.21.2'  }  # Demo 2: architecture (JS)
    @{ name = 'bottle';          url = 'https://github.com/bottlepy/bottle.git';     tag = '0.13.2'  }  # Demo 3: refactoring at scale (single-file framework)
    @{ name = 'minimist-1.2.5';  url = 'https://github.com/minimistjs/minimist.git'; tag = 'v1.2.5'  }  # Demo 4: CVE-2021-44906 (vulnerable)
    @{ name = 'minimist-1.2.6';  url = 'https://github.com/minimistjs/minimist.git'; tag = 'v1.2.6'  }  # Demo 4: fixed
    @{ name = 'requests-2.30.0'; url = 'https://github.com/psf/requests.git';        tag = 'v2.30.0' }  # Demo 4: CVE-2023-32681 (vulnerable)
    @{ name = 'requests-2.31.0'; url = 'https://github.com/psf/requests.git';        tag = 'v2.31.0' }  # Demo 4: fixed
)

if ($Only) {
    $targets = $targets | Where-Object { $n = $_.name; [bool]($Only | Where-Object { $n -like "$_*" }) }
}

foreach ($t in $targets) {
    $dest = Join-Path $targetsDir $t.name
    if (Test-Path $dest) { Write-Host "skip   $($t.name) (already present)"; continue }
    Write-Host "clone  $($t.name) @ $($t.tag)"
    git -c advice.detachedHead=false clone --quiet --depth 1 --branch $t.tag $t.url $dest
    if ($LASTEXITCODE -ne 0) { throw "Failed to clone $($t.name)" }
}

Write-Host "`nDone. Targets are in $targetsDir (git-ignored)."
