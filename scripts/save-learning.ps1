param(
    [switch]$Push,
    [string]$Message = ("study: " + (Get-Date -Format "yyyy-MM-dd HH:mm"))
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Push-Location $repo
try {
    $top = & git rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -ne 0 -or [IO.Path]::GetFullPath($top.Trim()) -ne [IO.Path]::GetFullPath($repo)) {
        throw 'Run this script only in its own initialized learning repository.'
    }
    & git var GIT_AUTHOR_IDENT *> $null
    if ($LASTEXITCODE -ne 0) { throw 'Configure repository-local Git author name and email first.' }
    $conflicts = & git diff --name-only --diff-filter=U
    if ($conflicts) { throw 'Resolve merge conflicts before saving.' }
    $allowed = @('README.md', '.gitignore', 'daily', 'docs', 'templates', 'exercises', 'scripts')
    & git add -- $allowed
    if ($LASTEXITCODE -ne 0) { throw 'git add failed.' }
    $names = @(& git -c core.quotepath=false diff --cached --name-only)
    foreach ($name in $names) {
        if ($name -notmatch '^(README\.md|\.gitignore|daily/|docs/|templates/|exercises/|scripts/)') {
            throw "Unexpected staged path: $name. Review the index manually."
        }
        if ($name -match '(^|/)(\.env($|\.)|credentials|secrets)|\.(pem|key|p12|pfx)$') {
            throw "Potential secret file: $name. Review and unstage it."
        }
        $size = & git cat-file -s ":$name" 2>$null
        if ($LASTEXITCODE -ne 0) { continue } # Deleted file
        if ([long]$size -gt 1MB) { throw "File exceeds learning repository limit: $name" }
        $content = (& git show ":$name") -join "`n"
        if ($content -match '(gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|sk-[A-Za-z0-9_-]{20,})') {
            throw "Potential credential in staged content: $name. Review and unstage it."
        }
    }
    & git diff --cached --check
    if ($LASTEXITCODE -ne 0) { throw 'Fix staged whitespace or conflict markers before saving.' }
    if ($names.Count -gt 0) {
        & git commit -m $Message
        if ($LASTEXITCODE -ne 0) { throw 'Commit failed; no push attempted.' }
    } else { Write-Host 'No new changes to commit.' }
    if ($Push) {
        & git remote get-url origin *> $null
        if ($LASTEXITCODE -ne 0) { throw 'Set the verified GitHub origin before uploading.' }
        & git push origin HEAD
        if ($LASTEXITCODE -ne 0) { throw 'Push failed. Local commits remain saved; resolve the error and retry.' }
    }
} finally { Pop-Location }
