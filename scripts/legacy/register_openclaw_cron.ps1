param(
    [Parameter(Mandatory=$true)][string]$Channel = "feishu",
    [Parameter(Mandatory=$true)][string]$To,
    [string]$Timezone = "Asia/Shanghai",
    [string]$Agent = "video-factory",
    [string]$ProjectRoot = "E:\project\OpenClaw_VideoFactory",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

$jobs = @(
    @{
        Name = "video-topic-selection"
        Cron = "30 8 * * *"
        Message = "进入 $ProjectRoot。使用 topic-intelligence 生成今日3到5个候选选题，只发送候选卡，不开始生产。"
    },
    @{
        Name = "video-auto-select-and-produce"
        Cron = "0 12 * * *"
        Message = "进入 $ProjectRoot。若今天已有用户选择，制作已选主题；若没有，且最高分达到门槛、来源核验通过、未重复，则自动选择最高分并立即制作。完成质量门禁后通过飞书发送提醒和待发布交付信息；不得发布抖音。"
    }
)

foreach ($job in $jobs) {
    $args = @(
        "cron", "add",
        "--name", $job.Name,
        "--cron", $job.Cron,
        "--tz", $Timezone,
        "--session", "isolated",
        "--agent", $Agent,
        "--message", $job.Message,
        "--announce",
        "--channel", $Channel,
        "--to", $To
    )
    Write-Host "openclaw $($args -join ' ')"
    if ($Apply) {
        & openclaw @args
        if ($LASTEXITCODE -ne 0) { throw "Failed to register $($job.Name)" }
    }
}

if (-not $Apply) {
    Write-Host ""
    Write-Host "Dry run only. Add -Apply after Feishu bot mode and target are confirmed."
}
