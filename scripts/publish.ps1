#requires -Version 7.0
<#
.SYNOPSIS
    Create the public GitHub repo (if missing) and push this repository. Idempotent.

.EXAMPLE
    pwsh ./scripts/publish.ps1
    pwsh ./scripts/publish.ps1 -RepoName semantic-gui-agent-testing -GitHubAccount Marica7731 -Private
#>
param(
    [string]$RepoName = "semantic-gui-agent-testing",
    [string]$GitHubAccount = "Marica7731",
    [switch]$Private
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) is required. Install it, then run: gh auth login"
}

gh auth status 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "GitHub CLI is not authenticated. Run: gh auth login"
}

if (-not (Test-Path .git)) {
    git init -b main
}

git add -A
git diff --cached --quiet
if ($LASTEXITCODE -ne 0) {
    git commit -m "feat: semantic GUI agent testing framework (Android/Windows executors, MCP server, docs)"
}

git remote get-url origin 2>$null
if ($LASTEXITCODE -ne 0) {
    $visibility = if ($Private) { "private" } else { "public" }
    gh repo create "$GitHubAccount/$RepoName" --$visibility --source . --remote origin --push
} else {
    git push -u origin main
}

Write-Host "Published: https://github.com/$GitHubAccount/$RepoName"
