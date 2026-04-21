param(
  [string]$Branch = "main"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $RepoRoot

git fetch --all --tags
git checkout $Branch
git pull --ff-only

$ReleaseId = $null
try {
  $ReleaseId = (git describe --tags --exact-match 2>$null).Trim()
} catch {
  $ReleaseId = $null
}
if ([string]::IsNullOrWhiteSpace($ReleaseId)) {
  $ReleaseId = (git rev-parse --short=12 HEAD).Trim()
}

$env:RELEASE_ID = $ReleaseId
Write-Host "Deploying RELEASE_ID=$ReleaseId on branch=$Branch"
docker compose up -d --build
Write-Host "Done."
