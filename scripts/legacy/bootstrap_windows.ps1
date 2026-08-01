$ErrorActionPreference = "Stop"

Write-Host "Checking dependencies..."
$required = @("python", "node", "npm", "ffmpeg", "ffprobe", "openclaw")
foreach ($bin in $required) {
    if (-not (Get-Command $bin -ErrorAction SilentlyContinue)) {
        Write-Warning "$bin is missing."
    } else {
        Write-Host "[OK] $bin"
    }
}

Write-Host "Checking NVIDIA..."
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    nvidia-smi
} else {
    Write-Warning "nvidia-smi not found. Install/update NVIDIA driver."
}

Write-Host "Creating Python venv..."
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\python.exe" -m pip install pyyaml typer rich

Write-Host "Optional GPU packages:"
Write-Host "  pip install faster-whisper"
Write-Host "  Install a CUDA-compatible PyTorch build appropriate for your driver."
Write-Host "Bootstrap complete."
