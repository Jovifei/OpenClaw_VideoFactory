param([switch]$Apply)
$ErrorActionPreference='Stop';if(-not(Get-Command openclaw -ErrorAction SilentlyContinue)){throw 'OpenClaw not installed.'}
$v=(& openclaw --version 2>&1|Out-String).Trim();Write-Host "OpenClaw version: $v";$m=[regex]::Match($v,'(\d{4}\.\d+\.\d+)');if($m.Success -and ([version]$m.Groups[1].Value -lt [version]'2026.5.29')){throw "Feishu requires OpenClaw 2026.5.29+. Current $($m.Groups[1].Value)"}
Write-Host 'openclaw channels login --channel feishu';Write-Host 'openclaw gateway restart';if(-not $Apply){Write-Host 'Dry run only.';exit 0}
& openclaw channels login --channel feishu;if($LASTEXITCODE -ne 0){throw 'Feishu setup failed.'};& openclaw gateway restart;if($LASTEXITCODE -ne 0){throw 'Gateway restart failed.'};& openclaw gateway status;& openclaw channels status
