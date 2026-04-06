param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$GitPushArgs
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvFile = Join-Path $ScriptDir "deploy-remote.env"

if (Test-Path $EnvFile) {
    Get-Content $EnvFile -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        if ($line -match '^\s*#' -or $line -eq "") { return }
        $eq = $line.IndexOf("=")
        if ($eq -lt 1) { return }
        $name = $line.Substring(0, $eq).Trim()
        $val = $line.Substring($eq + 1).Trim()
        if ($val.StartsWith('"') -and $val.EndsWith('"')) {
            $val = $val.Substring(1, $val.Length - 2)
        }
        Set-Item -Path "Env:$name" -Value $val
    }
}

$deployHost = $env:DEPLOY_HOST
$deployUser = $env:DEPLOY_USER
if (-not $deployHost -or -not $deployUser) {
    Write-Error "Set DEPLOY_HOST and DEPLOY_USER in scripts/deploy-remote.env (see deploy-remote.env.example)."
}

$port = if ($env:DEPLOY_SSH_PORT) { $env:DEPLOY_SSH_PORT } else { "22000" }
$remoteDir = if ($env:DEPLOY_REMOTE_DIR) { $env:DEPLOY_REMOTE_DIR } else { "~/Random-Notes" }

$repoRoot = Split-Path -Parent $ScriptDir
$defaultKeyPath = Join-Path $repoRoot "github_deploy"
$identityFile = if ($env:DEPLOY_SSH_KEY) { $env:DEPLOY_SSH_KEY }
elseif (Test-Path -LiteralPath $defaultKeyPath) { $defaultKeyPath }
else { $null }

if ($null -eq $GitPushArgs -or $GitPushArgs.Count -eq 0) {
    Write-Host "Running: git push"
    & git push
} else {
    Write-Host ("Running: git push " + ($GitPushArgs -join " "))
    & git push @GitPushArgs
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$target = "${deployUser}@${deployHost}"
$remoteShell = 'set -e; cd {0} && git pull --ff-only && cd deploy && docker compose up -d --build' -f $remoteDir

if (-not $identityFile) {
    Write-Error "SSH private key missing: repo-root github_deploy or DEPLOY_SSH_KEY in deploy-remote.env."
}

$sshArgs = @(
    "-p", $port,
    "-o", "BatchMode=yes",
    "-o", "ConnectTimeout=30",
    "-o", "IdentitiesOnly=yes",
    "-i", $identityFile
)
$sshArgs += @($target, $remoteShell)

Write-Host "SSH key: $identityFile"
Write-Host "Running: ssh -> $target"
& ssh @sshArgs
exit $LASTEXITCODE
