$ErrorActionPreference = "Continue"
$Root=Split-Path -Parent $PSScriptRoot
$Out=Join-Path $Root 'reports\openclaw_state'
New-Item -ItemType Directory -Force -Path $Out|Out-Null

function Redact-Text {
    param([string]$Text)
    if($null -eq $Text){return $null}
    $redacted=$Text
    $redacted=$redacted -replace '(?i)(app[_-]?secret|access[_-]?token|refresh[_-]?token|api[_-]?key|password)\s*[:=]\s*\S+','$1=[REDACTED]'
    return $redacted -replace 'sk-[A-Za-z0-9_-]{16,}','[REDACTED_KEY]'
}

function Capture {
    param([string]$Name,[string]$Command,[Alias('Args')][string[]]$CommandArgs,[int]$TimeoutSeconds=3)
    $path=Join-Path $Out ($Name+'.txt')
    $found=Get-Command $Command -ErrorAction SilentlyContinue
    if(-not $found){"COMMAND: $Command $($CommandArgs -join ' ')`nEXIT_CODE: command-not-found`nCOMMAND NOT FOUND: $Command"|Set-Content -Encoding UTF8 $path;return}
    $stdout=[IO.Path]::GetTempFileName();$stderr=[IO.Path]::GetTempFileName()
    try {
        $filePath=$found.Source;$argumentList=@($CommandArgs)
        if($found.CommandType -eq 'ExternalScript'){$filePath=Join-Path $PSHOME 'powershell.exe';$argumentList=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$found.Source)+@($CommandArgs)}
        $process=Start-Process -FilePath $filePath -ArgumentList $argumentList -NoNewWindow -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        if(-not $process.WaitForExit($TimeoutSeconds*1000)) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            $output=((Get-Content -Raw -ErrorAction SilentlyContinue $stdout),(Get-Content -Raw -ErrorAction SilentlyContinue $stderr)) -join [Environment]::NewLine
            "COMMAND: $Command $($CommandArgs -join ' ')`nEXIT_CODE: -2`nTIMED OUT after $TimeoutSeconds seconds`n$(Redact-Text $output)"|Set-Content -Encoding UTF8 $path
            return
        }
        $process.WaitForExit();$process.Refresh()
        $output=((Get-Content -Raw -ErrorAction SilentlyContinue $stdout),(Get-Content -Raw -ErrorAction SilentlyContinue $stderr)) -join [Environment]::NewLine
        "COMMAND: $Command $($CommandArgs -join ' ')`nEXIT_CODE: $($process.ExitCode)`n$(Redact-Text $output)"|Set-Content -Encoding UTF8 $path
    } catch {
        "COMMAND: $Command $($CommandArgs -join ' ')`nEXIT_CODE: -1`n$(Redact-Text $_.Exception.Message)"|Set-Content -Encoding UTF8 $path
    } finally {Remove-Item -LiteralPath $stdout,$stderr -Force -ErrorAction SilentlyContinue}
}

Capture -Name 'version' -Command 'openclaw' -Args @('--version')
Capture -Name 'config_schema' -Command 'openclaw' -Args @('config','schema')
Capture -Name 'config_validate' -Command 'openclaw' -Args @('config','validate')
Capture -Name 'doctor' -Command 'openclaw' -Args @('doctor')
Capture -Name 'gateway_status' -Command 'openclaw' -Args @('gateway','status')
Capture -Name 'status_all' -Command 'openclaw' -Args @('status','--all')
Capture -Name 'channels_status' -Command 'openclaw' -Args @('channels','status')
Capture -Name 'skills_check' -Command 'openclaw' -Args @('skills','check')
Capture -Name 'cron_list' -Command 'openclaw' -Args @('cron','list')
Capture -Name 'security_audit' -Command 'openclaw' -Args @('security','audit')

$paths=@('agents.defaults.workspace','agents.defaults.userTimezone','agents.defaults.skills','plugins.entries.codex.enabled','plugins.entries.codex.config.appServer.homeScope','tools.exec.mode','gateway.mode','gateway.bind','cron.enabled','cron.maxConcurrentRuns','channels.feishu.dmPolicy','channels.feishu.groupPolicy','channels.feishu.requireMention','channels.feishu.mediaMaxMb')
foreach($p in $paths){$n=($p -replace '[^A-Za-z0-9_.-]','_') -replace '\.','_';Capture -Name ('config_'+$n) -Command 'openclaw' -Args @('config','get',$p)}
Write-Host "OpenClaw state captured at $Out"
exit 0
