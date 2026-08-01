$repoRoot = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repoRoot '.venv\Scripts\python.exe'

Describe 'P1 offline candidate boundary' {
    It 'keeps the production factory entrypoint fail-closed' {
        $entrypoint = Join-Path $repoRoot 'scripts\factory.py'
        $startInfo = New-Object System.Diagnostics.ProcessStartInfo
        $startInfo.FileName = $python
        $startInfo.Arguments = ('"{0}"' -f $entrypoint)
        $startInfo.UseShellExecute = $false
        $startInfo.RedirectStandardOutput = $true
        $startInfo.RedirectStandardError = $true
        $process = New-Object System.Diagnostics.Process
        $process.StartInfo = $startInfo
        [void]$process.Start()
        [void]$process.StandardOutput.ReadToEnd()
        $stderr = $process.StandardError.ReadToEnd()
        $process.WaitForExit()
        $process.ExitCode | Should Be 78
        $stderr | Should Match 'production pipeline is not implemented'
    }

    It 'reports an offline-only doctor without OpenClaw or Feishu contact' {
        $raw = & $python (Join-Path $repoRoot 'scripts\factory.py') candidate doctor --json
        $doctor = $raw | ConvertFrom-Json
        $doctor.mode | Should Be 'offline_candidate'
        $doctor.openclaw_contacted | Should Be $false
        $doctor.feishu_contacted | Should Be $false
    }

    It 'contains exactly eight deterministic mascot source poses' {
        $poses = Get-ChildItem -LiteralPath (Join-Path $repoRoot 'src\factory\assets\mascot') -Filter '*.svg' -File
        $poses.Count | Should Be 8
    }

    It 'keeps delivery implementation dry-run only' {
        $source = Get-Content -LiteralPath (Join-Path $repoRoot 'src\factory\delivery.py') -Raw -Encoding UTF8
        $source | Should Match 'dry-run'
        $source | Should Not Match 'larksuite'
        $source | Should Not Match 'feishu send'
    }
}
