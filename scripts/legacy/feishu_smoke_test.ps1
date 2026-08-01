param(
    [Parameter(Mandatory=$true)][string]$ChatId,
    [switch]$Apply,
    [string]$DeliveryDir = "."
)

$ErrorActionPreference = "Stop"
Push-Location $DeliveryDir
try {
    $key = "video-factory-smoke-" + (Get-Date -Format "yyyyMMddHHmm")
    $args = @(
        "im", "+messages-send",
        "--as", "bot",
        "--chat-id", $ChatId,
        "--markdown", "## OpenClaw视频工厂`n`n飞书CLI消息测试通过。",
        "--idempotency-key", $key
    )
    if (-not $Apply) { $args += "--dry-run" }
    & lark-cli @args
    if ($LASTEXITCODE -ne 0) { throw "Message smoke test failed." }

    if (Test-Path ".\cover.png") {
        $args2 = @(
            "im", "+messages-send",
            "--as", "bot",
            "--chat-id", $ChatId,
            "--image", ".\cover.png",
            "--idempotency-key", ($key + "-cover")
        )
        if (-not $Apply) { $args2 += "--dry-run" }
        & lark-cli @args2
    }
} finally {
    Pop-Location
}

if (-not $Apply) {
    Write-Host "Dry run complete. Rerun with -Apply after verifying the target chat."
}
