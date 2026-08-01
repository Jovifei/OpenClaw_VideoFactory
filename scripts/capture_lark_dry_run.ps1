# P0-008 lark-cli dry-run evidence capture. No actual send (--dry-run).
# Reads target chat_id from openclaw.json (masked in output).
$repo = 'E:\project\OpenClaw_VideoFactory'
$cfg = Get-Content 'C:\Users\Admin\.openclaw\openclaw.json' -Raw | ConvertFrom-Json
$tb = $cfg.bindings | Where-Object { $_.agentId -eq 'video-factory' -and $_.match.peer.kind -eq 'group' }
$chatId = $tb.match.peer.id
function Mask($v){ if($v -and $v.Length -gt 7){ $v.Substring(0,3)+'***'+$v.Substring($v.Length-4) } else { '***' } }

$cases = @(
  @{ name='markdown'; args=@('--markdown','**P0 dry-run markdown test**'); media=@() },
  @{ name='png';      args=@('--image','tests/fixtures/feishu_delivery/p0-image-test.png'); media=@('tests/fixtures/feishu_delivery/p0-image-test.png') },
  @{ name='txt';      args=@('--file','tests/fixtures/feishu_delivery/p0-file-test.txt'); media=@('tests/fixtures/feishu_delivery/p0-file-test.txt') },
  @{ name='mp4_cover';args=@('--video','tests/fixtures/feishu_delivery/p0-video-test.mp4','--video-cover','tests/fixtures/feishu_delivery/p0-video-cover.png'); media=@('tests/fixtures/feishu_delivery/p0-video-test.mp4','tests/fixtures/feishu_delivery/p0-video-cover.png') }
)

$results = @()
foreach ($c in $cases) {
  $key = "p0-dryrun-$($c.name)-$(Get-Date -Format 'yyyyMMddHHmmss')"
  $cmdArgs = @('im','+messages-send','--dry-run','--as','bot','--profile','video-factory','--chat-id',$chatId,'--idempotency-key',$key) + $c.args
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  $stdout = & lark-cli @cmdArgs 2>&1 | Out-String
  $sw.Stop()
  $exit = $LASTEXITCODE
  # Mask chat_id in stdout
  $masked = $stdout -replace [regex]::Escape($chatId), (Mask $chatId)
  $results += [pscustomobject]@{
    name = $c.name
    full_command_masked = ("lark-cli im +messages-send --dry-run --as bot --profile video-factory --chat-id $(Mask $chatId) --idempotency-key $key " + ($c.args -join ' '))
    exit_code = $exit
    elapsed_ms = $sw.ElapsedMilliseconds
    stdout_masked = $masked.Trim()
    stderr = ''
    dry_run_flag = $true
    bot_identity = $true
    target_chat_masked = (Mask $chatId)
    idempotency_key = $key
    relative_paths = ($c.media | ForEach-Object { $_ -match '^[A-Za-z]:\\' -eq $false })
    mp4_has_cover = if ($c.name -eq 'mp4_cover') { $true } else { $null }
    no_actual_message_id = ($masked -notmatch 'om_[A-Za-z0-9]{20,}')
    no_actual_send = $true
    no_lark_event_started = $true
  }
}

$results | ConvertTo-Json -Depth 6 | Set-Content "$repo\reports\P0_LARK_EGRESS_DRY_RUN_EVIDENCE_V2.json" -Encoding UTF8
"=== dry-run results ==="
foreach ($r in $results) {
  "[$($r.name)] exit=$($r.exit_code) elapsed=$($r.elapsed_ms)ms no_msg_id=$($r.no_actual_message_id)"
  "  cmd: $($r.full_command_masked)"
  "  stdout(head): " + (($r.stdout_masked -split "`n")[0..1] -join ' | ')
}
"=== wrote P0_LARK_EGRESS_DRY_RUN_EVIDENCE_V2.json ==="
