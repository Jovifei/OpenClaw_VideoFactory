param([switch]$Apply)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    & $VenvPython -c "import yaml; print('PyYAML', yaml.__version__)"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Bootstrap environment is already ready."
        exit 0
    }
}

$PythonCommand = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCommand = @("py", "-3.11")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCommand = @("python")
} else {
    throw "Python is not installed. Install Python 3.11 before continuing."
}

Write-Host "Planned project-local bootstrap:"
Write-Host "  create .venv"
Write-Host "  install requirements-bootstrap.txt"

if (-not $Apply) {
    Write-Host "Dry run only. Rerun with -Apply."
    exit 0
}

if ($PythonCommand.Count -eq 2) {
    & $PythonCommand[0] $PythonCommand[1] -m venv (Join-Path $Root ".venv")
} else {
    & $PythonCommand[0] -m venv (Join-Path $Root ".venv")
}
if ($LASTEXITCODE -ne 0) { throw "Could not create .venv." }

& $VenvPython -m pip install --disable-pip-version-check -r (Join-Path $Root "requirements-bootstrap.txt")
if ($LASTEXITCODE -ne 0) { throw "Could not install bootstrap requirements." }

& $VenvPython -c "import yaml; print('PyYAML', yaml.__version__)"
if ($LASTEXITCODE -ne 0) { throw "Bootstrap validation failed." }
