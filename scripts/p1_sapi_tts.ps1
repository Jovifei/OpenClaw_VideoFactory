param(
    [Parameter(Mandatory=$true)][string]$InputTextPath,
    [Parameter(Mandatory=$true)][string]$OutputPath,
    [Parameter(Mandatory=$true)][string]$VoiceName
)

$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $InputTextPath -PathType Leaf)) { throw 'input_text_missing' }
$text = Get-Content -LiteralPath $InputTextPath -Raw -Encoding UTF8
if ([string]::IsNullOrWhiteSpace($text)) { throw 'input_text_empty' }
Add-Type -AssemblyName System.Speech
$parent = Split-Path -Parent $OutputPath
New-Item -ItemType Directory -Path $parent -Force | Out-Null
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $speaker.SelectVoice($VoiceName)
    $speaker.SetOutputToWaveFile($OutputPath)
    $speaker.Speak($text)
} finally {
    $speaker.Dispose()
}
