param([string]$Profile='video-factory',[switch]$StartAppConfiguration,[switch]$StartUserDriveDocsAuth,[switch]$CheckStatus)
$ErrorActionPreference='Stop';if(-not(Get-Command lark-cli -ErrorAction SilentlyContinue)){throw 'lark-cli not installed.'}
if($StartAppConfiguration){& lark-cli config init --name $Profile;if($LASTEXITCODE -ne 0){throw 'App configuration failed.'}}
if($StartUserDriveDocsAuth){& lark-cli auth login --profile $Profile --domain drive --domain docs --no-wait --json;if($LASTEXITCODE -ne 0){throw 'Could not start auth.'};Write-Host 'Show URL and QR to user; wait for user confirmation before device-code polling.'}
if($CheckStatus -or (-not $StartAppConfiguration -and -not $StartUserDriveDocsAuth)){& lark-cli auth status --profile $Profile --verify;if($LASTEXITCODE -ne 0){throw 'lark-cli auth status failed.'};& lark-cli doctor --profile $Profile;if($LASTEXITCODE -ne 0){throw 'lark-cli doctor failed.'}}
