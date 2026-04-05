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
    Write-Error "缺少 DEPLOY_HOST 或 DEPLOY_USER。复制 deploy-remote.env.example 为 deploy-remote.env 并填写。"
}

$port = if ($env:DEPLOY_SSH_PORT) { $env:DEPLOY_SSH_PORT } else { "22000" }
$remoteDir = if ($env:DEPLOY_REMOTE_DIR) { $env:DEPLOY_REMOTE_DIR } else { "~/Random-Notes" }

if ($null -eq $GitPushArgs -or $GitPushArgs.Count -eq 0) {
    Write-Host "执行: git push"
    & git push
} else {
    Write-Host ("执行: git push " + ($GitPushArgs -join " "))
    & git push @GitPushArgs
}
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$target = "${deployUser}@${deployHost}"
$remoteShell = "set -e; cd $remoteDir && git pull --ff-only && cd deploy && docker compose up -d --build"

$sshArgs = @("-p", $port, "-o", "BatchMode=yes", "-o", "ConnectTimeout=30")
if ($env:DEPLOY_SSH_KEY) {
    $sshArgs += @("-i", $env:DEPLOY_SSH_KEY)
}
$sshArgs += @($target, $remoteShell)

Write-Host ("执行: ssh ... $target")
& ssh @sshArgs
exit $LASTEXITCODE
