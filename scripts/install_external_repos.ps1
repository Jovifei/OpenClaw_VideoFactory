param(
    [switch]$ReviewedLicenses,
    [string]$ExternalRoot = "$PSScriptRoot\..\external"
)

$ErrorActionPreference = "Stop"

if (-not $ReviewedLicenses) {
    Write-Host "This script only clones source. It will not install or execute third-party code."
    Write-Host "Read docs\SECURE_INSTALL_GUIDE.md and rerun with -ReviewedLicenses."
    exit 2
}

New-Item -ItemType Directory -Force -Path $ExternalRoot | Out-Null

function Clone-Repo {
    param([string]$Name, [string]$Url, [string]$Ref = "")
    $Target = Join-Path $ExternalRoot $Name
    if (Test-Path $Target) {
        Write-Host "[SKIP] $Name already exists: $Target"
        return
    }
    Write-Host "[CLONE] $Name"
    if ($Ref) {
        git clone --depth 1 --branch $Ref $Url $Target
    } else {
        git clone --depth 1 $Url $Target
    }
}

Clone-Repo "remotion-skills" "https://github.com/remotion-dev/skills.git"
Clone-Repo "video-podcast-maker" "https://github.com/Agents365-ai/video-podcast-maker.git" "v2.3.0"
Clone-Repo "comfyui-mcp" "https://github.com/artokun/comfyui-mcp.git" "v0.30.0"
Clone-Repo "capcut-mate" "https://github.com/Hommy-master/capcut-mate.git" "v8.0.69"
Clone-Repo "jianying-editor-skill" "https://github.com/luoluoluo22/jianying-editor-skill.git"
Clone-Repo "ian-fenzhu-illustrations" "https://github.com/Jovifei/ian-fenzhu-illustrations.git"

Write-Host ""
Write-Host "Cloning is complete. No dependency installer was executed."
Write-Host "Review each LICENSE, SKILL.md, lock file, and scripts before enabling it."
