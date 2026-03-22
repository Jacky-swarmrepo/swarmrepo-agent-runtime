$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
Set-Location $RepoRoot

if (-not (Test-Path ".env")) {
    Write-Host "Missing .env in $RepoRoot"
    Write-Host "Copy .env.example to .env and fill the local BYOK values first."
    exit 1
}

if ($env:PYTHON_BIN) {
    $pythonExe = $env:PYTHON_BIN
    $pythonArgs = @()
}
elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonExe = "py"
    $pythonArgs = @("-3")
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = "python"
    $pythonArgs = @()
}
else {
    Write-Host "Python was not found."
    Write-Host "Install Python 3.11+ and try again."
    exit 1
}

& $pythonExe @pythonArgs -c "import httpx, dotenv, swarmrepo_sdk" *> $null
if ($LASTEXITCODE -ne 0) {
    $joinedArgs = ""
    if ($pythonArgs.Count -gt 0) {
        $joinedArgs = ($pythonArgs -join " ") + " "
    }
    Write-Host "Missing Python dependencies for swarmrepo-agent-runtime."
    Write-Host "For private-repo validation, install specs, SDK, and runtime first:"
    Write-Host ("  {0} {1}-m pip install -e /path/to/swarmrepo-specs" -f $pythonExe, $joinedArgs)
    Write-Host ("  {0} {1}-m pip install -e /path/to/swarmrepo-sdk" -f $pythonExe, $joinedArgs)
    Write-Host ("  {0} {1}-m pip install -e ." -f $pythonExe, $joinedArgs)
    exit 1
}

if ($env:PYTHONPATH) {
    $env:PYTHONPATH = "$RepoRoot/src;$env:PYTHONPATH"
}
else {
    $env:PYTHONPATH = "$RepoRoot/src"
}

Write-Host "Starting SwarmRepo custom agent template from $RepoRoot"
& $pythonExe @pythonArgs "-m" "swarmrepo_agent_runtime.custom_agent_template"
exit $LASTEXITCODE
