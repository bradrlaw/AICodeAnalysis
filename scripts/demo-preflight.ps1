<#
.SYNOPSIS
  Pre-flight check for the live demos. Run it ~30 minutes before the lecture. Everything should be green.
#>
$root = Split-Path -Parent $PSScriptRoot
$fail = 0
$warn = 0
function Check($name, [scriptblock]$test, $hint, [switch]$Optional) {
    $ok = $false; $err = $null; try { $ok = [bool](& $test) } catch { $err = $_.Exception.Message }
    if ($ok) { Write-Host "  [OK]   $name" -ForegroundColor Green }
    elseif ($Optional) { Write-Host "  [WARN] $name  ->  $hint" -ForegroundColor Yellow; $script:warn++ }
    else { Write-Host "  [FAIL] $name  ->  $hint" -ForegroundColor Red; if ($err) { Write-Host "         ($err)" -ForegroundColor DarkGray }; $script:fail++ }
}

Write-Host "`nTools" -ForegroundColor Cyan
Check 'Copilot CLI'          { Get-Command copilot -ErrorAction Stop }  'winget install GitHub.Copilot'
Check 'CodeQL CLI on PATH'   { Get-Command codeql -ErrorAction Stop }   "Open a NEW terminal (PATH was updated) or add $env:LOCALAPPDATA\codeql-bundle\codeql to PATH"
Check 'VS Code'              { Get-Command code -ErrorAction Stop }     'Install VS Code'
Check 'VS Code: Mermaid ext' { (code --list-extensions) -contains 'bierner.markdown-mermaid' } 'code --install-extension bierner.markdown-mermaid'
Check 'VS Code: SARIF ext'   { (code --list-extensions) -contains 'ms-sarifvscode.sarif-viewer' } 'code --install-extension MS-SarifVSCode.sarif-viewer'
Check 'gh signed in'         { gh auth status 2>&1 | Select-String 'Logged in' } 'gh auth login'

Write-Host "`nTargets & labs" -ForegroundColor Cyan
foreach ($t in 'tinydb','express','flask','bottle','minimist-1.2.5','minimist-1.2.6','requests-2.30.0','requests-2.31.0') {
    Check "targets\$t" { Test-Path (Join-Path $root "targets\$t") } 'scripts\setup-targets.ps1'
}
Check 'Python venv with Flask' { & (Join-Path $root '.venv\Scripts\python.exe') -c 'import flask' 2>$null; $LASTEXITCODE -eq 0 } 'python -m venv .venv; .venv\Scripts\pip install -r labs\vuln-notes-flask\requirements.txt'
Check 'Express lab deps'       { Test-Path (Join-Path $root 'labs\vuln-notes-express\node_modules\express') } 'cd labs\vuln-notes-express; npm install'
Check 'tape (minimist tests)'  { Test-Path (Join-Path $root 'node_modules\tape') } 'npm install (repo root)'
Check 'legacy-invoice tests'   { $p = Start-Process python -ArgumentList '-m','unittest','-q' -WorkingDirectory (Join-Path $root 'labs\legacy-invoice') -NoNewWindow -Wait -PassThru -RedirectStandardError "$env:TEMP\preflight-unittest.txt"; $p.ExitCode -eq 0 } 'python -m unittest -v in labs\legacy-invoice'

Write-Host "`nPre-built CodeQL results" -ForegroundColor Cyan
foreach ($f in 'codeql-db-flask','codeql-db-express','flask.sarif','express.sarif') {
    Check $f { Test-Path (Join-Path $root $f) } 'See docs\demo-script.md > Prep: CodeQL'
}

Write-Host "`nSlides & GitHub" -ForegroundColor Cyan
Check 'dist\lecture.html'  { Test-Path (Join-Path $root 'dist\lecture.html') } 'npm run build'
Check 'dist\lecture.pptx'  { Test-Path (Join-Path $root 'dist\lecture.pptx') } 'npm run build:pptx'
foreach ($n in 1, 2) {
    Check "Demo PR #$n is open" { (gh pr view $n --repo bradrlaw/AICodeAnalysis-demo-labs --json state -q .state) -eq 'OPEN' } 'See docs\demo-script.md > Prep: GitHub'
}
Check 'Copilot review on PR #1' { gh api repos/bradrlaw/AICodeAnalysis-demo-labs/pulls/1/reviews -q '.[].user.login' | Select-String -SimpleMatch 'copilot' } 'Web UI: PR #1 > Reviewers > Copilot (takes 1-3 min)'
Check 'Autofix on PR #2'        { gh api repos/bradrlaw/AICodeAnalysis-demo-labs/pulls/2/comments -q '.[].body' | Select-String -Pattern 'Autofix|```suggestion' } 'Optional: PR #2 > Files changed > alert "Show more details" > Generate fix (web UI only)' -Optional

Write-Host ""
if ($fail) { Write-Host "$fail check(s) failed." -ForegroundColor Red; exit 1 }
elseif ($warn) { Write-Host "All required demo prerequisites ready ($warn optional warning(s))." -ForegroundColor Yellow }
else { Write-Host 'All demo prerequisites ready.' -ForegroundColor Green }
