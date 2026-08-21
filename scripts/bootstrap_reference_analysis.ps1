param(
    [string]$Python312 = 'C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe',
    [string]$WheelDirectory = 'E:\Claude_allow\Download\OpenClaw_VideoFactory-wheels'
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $repoRoot '.venv-reference-analysis'
$requirements = Join-Path $repoRoot 'requirements\reference-analysis.txt'

if (-not (Test-Path -LiteralPath $Python312 -PathType Leaf)) {
    throw "Python 3.12 executable is unavailable."
}
if (-not (Test-Path -LiteralPath $WheelDirectory -PathType Container)) {
    throw "Approved wheel directory is unavailable; network download is forbidden."
}
if (-not (Test-Path -LiteralPath (Join-Path $venv 'Scripts\python.exe') -PathType Leaf)) {
    & $Python312 -m venv $venv
}
$venvPython = Join-Path $venv 'Scripts\python.exe'
& $venvPython -m pip install --no-index --find-links $WheelDirectory -r $requirements
& $venvPython -c "import scenedetect, faster_whisper; print('reference-analysis-environment-ok')"
