$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Reports = Join-Path $Root "reports"
New-Item -ItemType Directory -Force -Path $Reports | Out-Null

function Run-Capture {
    param([string]$Command, [string[]]$Args = @())
    $found = Get-Command $Command -ErrorAction SilentlyContinue
    if (-not $found) {
        return [ordered]@{ found = $false; path = $null; output = $null; exitCode = $null }
    }
    try {
        $out = & $Command @Args 2>&1 | Out-String
        return [ordered]@{
            found = $true
            path = $found.Source
            output = $out.Trim()
            exitCode = $LASTEXITCODE
        }
    } catch {
        return [ordered]@{
            found = $true
            path = $found.Source
            output = $_.Exception.Message
            exitCode = -1
        }
    }
}

$os = Get-CimInstance Win32_OperatingSystem
$computer = Get-CimInstance Win32_ComputerSystem
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$disks = Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    [ordered]@{
        drive = $_.DeviceID
        sizeGB = [math]::Round($_.Size / 1GB, 1)
        freeGB = [math]::Round($_.FreeSpace / 1GB, 1)
    }
}

$tools = [ordered]@{}
$tools.node = Run-Capture "node" @("--version")
$tools.npm = Run-Capture "npm" @("--version")
$tools.python = Run-Capture "python" @("--version")
$tools.git = Run-Capture "git" @("--version")
$tools.ffmpeg = Run-Capture "ffmpeg" @("-version")
$tools.ffprobe = Run-Capture "ffprobe" @("-version")
$tools.openclaw = Run-Capture "openclaw" @("--version")
$tools.openclawGateway = Run-Capture "openclaw" @("gateway", "status", "--json")
$tools.openclawDoctor = Run-Capture "openclaw" @("doctor")
$tools.openclawCron = Run-Capture "openclaw" @("cron", "list")
$tools.openclawSkills = Run-Capture "openclaw" @("skills", "check")
$tools.codex = Run-Capture "codex" @("--version")
$tools.larkCli = Run-Capture "lark-cli" @("--version")
$tools.larkAuth = Run-Capture "lark-cli" @("auth", "status", "--json", "--verify")
$tools.nvidia = Run-Capture "nvidia-smi" @("--query-gpu=name,driver_version,memory.total,memory.free", "--format=csv,noheader")
$tools.ffmpegNvenc = Run-Capture "ffmpeg" @("-hide_banner", "-encoders")


$comfyCandidates = @()
$commonComfyPaths = @(
    "$env:USERPROFILE\ComfyUI",
    "$env:USERPROFILE\ComfyUI_windows_portable",
    "C:\ComfyUI",
    "D:\ComfyUI",
    "E:\ComfyUI",
    "E:\project\ComfyUI",
    "E:\project\ComfyUI_windows_portable"
)
foreach ($candidate in $commonComfyPaths) {
    if (Test-Path $candidate) {
        $comfyCandidates += [ordered]@{ source = "common_path"; path = $candidate }
    }
}
try {
    Get-CimInstance Win32_Process | Where-Object {
        $_.CommandLine -and ($_.CommandLine -match "ComfyUI|main\.py.*8188")
    } | ForEach-Object {
        $comfyCandidates += [ordered]@{
            source = "running_process"
            processId = $_.ProcessId
            name = $_.Name
            commandLine = $_.CommandLine
        }
    }
} catch {}

$ports = [ordered]@{}
foreach ($p in @(8188, 30000, 18789)) {
    try {
        $test = Test-NetConnection -ComputerName 127.0.0.1 -Port $p -WarningAction SilentlyContinue
        $ports["$p"] = [bool]$test.TcpTestSucceeded
    } catch {
        $ports["$p"] = $false
    }
}

$inventory = [ordered]@{
    generatedAt = (Get-Date).ToString("o")
    note = "Read-only inventory. Secret values are not collected."
    os = [ordered]@{
        caption = $os.Caption
        version = $os.Version
        buildNumber = $os.BuildNumber
        architecture = $os.OSArchitecture
        timeZone = (Get-TimeZone).Id
    }
    hardware = [ordered]@{
        manufacturer = $computer.Manufacturer
        model = $computer.Model
        ramGB = [math]::Round($computer.TotalPhysicalMemory / 1GB, 1)
        cpu = $cpu.Name
        disks = $disks
    }
    tools = $tools
    loopbackPorts = $ports
    comfyuiDiscovery = $comfyCandidates
    secretPresenceOnly = [ordered]@{
        OPENAI_API_KEY = [bool]$env:OPENAI_API_KEY
        CODEX_API_KEY = [bool]$env:CODEX_API_KEY
        TELEGRAM_BOT_TOKEN = [bool]$env:TELEGRAM_BOT_TOKEN
    }
}

$jsonPath = Join-Path $Reports "machine_inventory.json"
$inventory | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 $jsonPath

$nvenc = $false
if ($tools.ffmpegNvenc.output -match "h264_nvenc") { $nvenc = $true }

$md = @()
$md += "# Machine Inventory"
$md += ""
$md += "- Generated: $($inventory.generatedAt)"
$md += "- OS: $($os.Caption) $($os.Version) ($($os.OSArchitecture))"
$md += "- Timezone: $((Get-TimeZone).Id)"
$md += "- RAM: $($inventory.hardware.ramGB) GB"
$md += "- CPU: $($cpu.Name)"
$md += "- GPU: $($tools.nvidia.output)"
$md += "- FFmpeg h264_nvenc detected: $nvenc"
$md += "- OpenClaw: $($tools.openclaw.output)"
$md += "- Codex: $($tools.codex.output)"
$md += "- lark-cli: $($tools.larkCli.output)"
$md += "- ComfyUI candidates: $($comfyCandidates.Count)"
$md += ""
$md += "## Loopback ports"
foreach ($k in $ports.Keys) { $md += "- $k : $($ports[$k])" }
$md += ""
$md += "## Disk"
foreach ($d in $disks) { $md += "- $($d.drive): $($d.freeGB) GB free / $($d.sizeGB) GB" }
$md += ""
$md += "## Notes"
$md += "- This report does not include token or key values."
$md += "- Review machine_inventory.json for detailed command outputs."
$mdPath = Join-Path $Reports "machine_inventory.md"
$md -join "`r`n" | Set-Content -Encoding UTF8 $mdPath

Write-Host "Created:"
Write-Host "  $jsonPath"
Write-Host "  $mdPath"
