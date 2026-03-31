$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
Set-Location $RepoRoot

Write-Host "swarmrepo-agent-runtime 0.1.2 is a helper-only public release."
Write-Host "The full agent daemon entrypoint is intentionally deferred."
Write-Host "Use scripts/start_custom_agent.ps1 for the reviewed public starter, and wait for a later reviewed release before expecting a public daemon here."
