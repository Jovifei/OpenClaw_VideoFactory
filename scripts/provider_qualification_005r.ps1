[CmdletBinding()]
param(
    [ValidateSet('Preflight', 'Start', 'Supervisor', 'Worker', 'Status', 'Verify')][string]$Mode = 'Preflight',
    [switch]$Apply,
    [switch]$Finalize,
    [string]$RunManifest
)

# Historical compatibility entry point.  005R was closed after its single
# Worker died; execution modes are intentionally rejected by the generic
# profile engine.  Preflight and Verify remain read-only.
$generic = Join-Path $PSScriptRoot 'provider_qualification.ps1'
$arguments = @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-File', $generic,
    '-QualificationProfile', '005R',
    '-Mode', $Mode
)
if ($Apply) { $arguments += '-Apply' }
if ($Finalize) { $arguments += '-Finalize' }
if (-not [string]::IsNullOrWhiteSpace($RunManifest)) {
    $arguments += @('-RunManifest', $RunManifest)
}

& 'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe' @arguments
exit $LASTEXITCODE
