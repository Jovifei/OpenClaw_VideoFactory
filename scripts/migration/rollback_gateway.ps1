[CmdletBinding()]
param([switch]$Simulate = $true)
if (-not $Simulate) { throw 'rollback requires separately approved maintenance authority; only -Simulate is available in P0.' }
[ordered]@{status='simulated';steps=@('stop_project_gateway','confirm_project_exit','restore_core_binding_operator_step','verify_text_path','verify_attachment_path');binding_changed=$false;gateway_restarted=$false} | ConvertTo-Json -Compress
