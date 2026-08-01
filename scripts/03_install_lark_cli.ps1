param([string]$Version='latest',[switch]$Apply)
$ErrorActionPreference='Stop';if(-not(Get-Command node -ErrorAction SilentlyContinue)){throw 'Node.js required.'};if(-not(Get-Command npx -ErrorAction SilentlyContinue)){throw 'npx required.'}
Write-Host "npx @larksuite/cli@$Version install";if(-not $Apply){Write-Host 'Dry run only. Rerun with -Apply.';exit 0}
& npx "@larksuite/cli@$Version" install;if($LASTEXITCODE -ne 0){throw 'lark-cli install failed.'};& lark-cli --version;if($LASTEXITCODE -ne 0){throw 'lark-cli not on PATH.'};Write-Host 'Record version in config\versions.lock.yaml.'
