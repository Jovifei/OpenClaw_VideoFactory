$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Reports = Join-Path $Root "reports"
New-Item -ItemType Directory -Force -Path $Reports | Out-Null
function Redact-Text { param([string]$Text); if ($null -eq $Text) { return $null }; $r=$Text; $r=$r -replace '(?i)(app[_-]?secret|access[_-]?token|refresh[_-]?token|api[_-]?key|password)\s*[:=]\s*\S+','$1=[REDACTED]'; $r=$r -replace 'sk-[A-Za-z0-9_-]{16,}','[REDACTED_KEY]'; return $r }
function Run-Capture {
    param([string]$Command,[Alias('Args')][string[]]$CommandArgs=@(),[int]$TimeoutSeconds=3)
    $found=Get-Command $Command -ErrorAction SilentlyContinue
    if(-not $found){return [ordered]@{found=$false;path=$null;output=$null;exitCode=$null}}
    $stdout=[IO.Path]::GetTempFileName();$stderr=[IO.Path]::GetTempFileName()
    try {
        $filePath=$found.Source;$argumentList=@($CommandArgs)
        if($found.CommandType -eq 'ExternalScript') {
            $filePath=Join-Path $PSHOME 'powershell.exe'
            $argumentList=@('-NoProfile','-ExecutionPolicy','Bypass','-File',$found.Source)+@($CommandArgs)
        }
        $process=Start-Process -FilePath $filePath -ArgumentList $argumentList -NoNewWindow -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
        if(-not $process.WaitForExit($TimeoutSeconds*1000)) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            $partial=((Get-Content -Raw -ErrorAction SilentlyContinue $stdout),(Get-Content -Raw -ErrorAction SilentlyContinue $stderr)) -join [Environment]::NewLine
            return [ordered]@{found=$true;path=$found.Source;output=(Redact-Text ("TIMED OUT after $TimeoutSeconds seconds`n$partial").Trim());exitCode=-2}
        }
        $process.WaitForExit()
        $process.Refresh()
        $out=((Get-Content -Raw -ErrorAction SilentlyContinue $stdout),(Get-Content -Raw -ErrorAction SilentlyContinue $stderr)) -join [Environment]::NewLine
        return [ordered]@{found=$true;path=$found.Source;output=(Redact-Text $out.Trim());exitCode=[int]$process.ExitCode}
    }catch{return [ordered]@{found=$true;path=$found.Source;output=(Redact-Text $_.Exception.Message);exitCode=-1}}
    finally{Remove-Item -LiteralPath $stdout,$stderr -Force -ErrorAction SilentlyContinue}
}
$os=Get-CimInstance Win32_OperatingSystem; $computer=Get-CimInstance Win32_ComputerSystem; $cpu=Get-CimInstance Win32_Processor|Select-Object -First 1
$disks=Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3"|ForEach-Object{[ordered]@{drive=$_.DeviceID;sizeGB=[math]::Round($_.Size/1GB,1);freeGB=[math]::Round($_.FreeSpace/1GB,1)}}
$tools=[ordered]@{}
$tools.powershell=[ordered]@{found=$true;path=$PSHOME;output=$PSVersionTable.PSVersion.ToString();exitCode=0}
$tools.node=Run-Capture -Command 'node' -Args @('--version');$tools.npm=Run-Capture -Command 'npm' -Args @('--version');$tools.npx=Run-Capture -Command 'npx' -Args @('--version');$tools.python=Run-Capture -Command 'python' -Args @('--version');$tools.git=Run-Capture -Command 'git' -Args @('--version')
$tools.ffmpeg=Run-Capture -Command 'ffmpeg' -Args @('-version');$tools.ffprobe=Run-Capture -Command 'ffprobe' -Args @('-version');$tools.openclaw=Run-Capture -Command 'openclaw' -Args @('--version')
$tools.codex=Run-Capture -Command 'codex' -Args @('--version');$tools.larkCli=Run-Capture -Command 'lark-cli' -Args @('--version');$tools.larkAuth=Run-Capture -Command 'lark-cli' -Args @('auth','status','--json','--verify')
$tools.nvidia=Run-Capture -Command 'nvidia-smi' -Args @('--query-gpu=name,driver_version,memory.total,memory.free,temperature.gpu','--format=csv,noheader');$tools.ffmpegEncoders=Run-Capture -Command 'ffmpeg' -Args @('-hide_banner','-encoders')
$comfy=@();$paths=@("$env:USERPROFILE\ComfyUI","$env:USERPROFILE\ComfyUI_windows_portable","C:\ComfyUI","D:\ComfyUI","E:\ComfyUI","E:\project\ComfyUI","E:\project\ComfyUI_windows_portable")
foreach($p in $paths){if(Test-Path $p){$comfy+=[ordered]@{source='common_path';path=$p}}}
try{Get-CimInstance Win32_Process|Where-Object{$_.Name -match 'python|pythonw' -and $_.CommandLine -match 'ComfyUI|main\.py'}|ForEach-Object{$comfy+=[ordered]@{source='running_process';processId=$_.ProcessId;executablePath=$_.ExecutablePath;commandLine=(Redact-Text $_.CommandLine)}}}catch{}
$jianying=@();$roots=@('HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*','HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*')
foreach($p in $roots){try{Get-ItemProperty $p -ErrorAction SilentlyContinue|Where-Object{$_.DisplayName -match '剪映|CapCut'}|ForEach-Object{$jianying+=[ordered]@{displayName=$_.DisplayName;displayVersion=$_.DisplayVersion;installLocation=$_.InstallLocation;publisher=$_.Publisher}}}catch{}}
$ports=[ordered]@{};foreach($port in @(18789,8188,30000)){try{$t=Test-NetConnection 127.0.0.1 -Port $port -WarningAction SilentlyContinue;$ports["$port"]=[bool]$t.TcpTestSucceeded}catch{$ports["$port"]=$false}}
$nvenc=$tools.ffmpegEncoders.output -match 'h264_nvenc';$blockers=@();foreach($n in @('node','npm','python','git','ffmpeg','ffprobe','openclaw')){if(-not $tools[$n].found){$blockers+="Missing command: $n"}};if(-not $tools.nvidia.found -or $tools.nvidia.exitCode -ne 0){$blockers+='NVIDIA GPU/driver not detected.'};if(-not $nvenc){$blockers+='h264_nvenc not detected.'}
$inventory=[ordered]@{generatedAt=(Get-Date).ToString('o');projectRoot=$Root;note='Read-only. No secret values.';os=[ordered]@{caption=$os.Caption;version=$os.Version;buildNumber=$os.BuildNumber;architecture=$os.OSArchitecture;timeZone=(Get-TimeZone).Id};hardware=[ordered]@{manufacturer=$computer.Manufacturer;model=$computer.Model;ramGB=[math]::Round($computer.TotalPhysicalMemory/1GB,1);cpu=$cpu.Name;disks=$disks};tools=$tools;capabilities=[ordered]@{h264Nvenc=$nvenc};loopbackPorts=$ports;comfyuiDiscovery=$comfy;jianyingDiscovery=$jianying;secretPresenceOnly=[ordered]@{OPENAI_API_KEY=[bool]$env:OPENAI_API_KEY;CODEX_API_KEY=[bool]$env:CODEX_API_KEY;FEISHU_APP_ID=[bool]$env:FEISHU_APP_ID;FEISHU_APP_SECRET=[bool]$env:FEISHU_APP_SECRET};blockers=$blockers}
$json=Join-Path $Reports 'machine_inventory.json';$inventory|ConvertTo-Json -Depth 10|Set-Content -Encoding UTF8 $json
$md=@('# Machine Inventory','',"- Generated: $($inventory.generatedAt)","- Project root: $Root","- OS: $($os.Caption) $($os.Version)","- Timezone: $((Get-TimeZone).Id)","- RAM: $($inventory.hardware.ramGB) GB","- CPU: $($cpu.Name)","- GPU: $($tools.nvidia.output)","- h264_nvenc: $nvenc","- OpenClaw: $($tools.openclaw.output)","- Codex: $($tools.codex.output)","- lark-cli: $($tools.larkCli.output)","- ComfyUI candidates: $($comfy.Count)","- Jianying candidates: $($jianying.Count)",'','## Blockers')
if($blockers.Count -eq 0){$md+='- None detected.'}else{foreach($b in $blockers){$md+="- $b"}}
$mdPath=Join-Path $Reports 'machine_inventory.md';$md -join "`r`n"|Set-Content -Encoding UTF8 $mdPath
Write-Host "Created $json and $mdPath";if($blockers.Count -gt 0){exit 2}else{exit 0}
