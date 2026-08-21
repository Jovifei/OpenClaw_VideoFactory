Set-StrictMode -Version Latest

# Compatibility surface for historical 005R read-only tests.  New execution
# uses ProviderQualification.psm1 and permanently rejects 005R Start.
Import-Module (Join-Path $PSScriptRoot 'ProviderQualification.psm1') -Force -WarningAction SilentlyContinue

function Get-Sha256([string]$Path) {
    return Get-PQSha256 -Path $Path
}

function Write-JsonAtomic {
    param([Parameter(Mandatory)][string]$Path, [Parameter(Mandatory)]$Value)
    Write-PQJsonAtomic -Path $Path -Value $Value
}

function New-InitialState([string]$RunId) {
    return New-PQInitialState -Profile (Get-PQProfile -QualificationProfile '005R') -RunId $RunId
}

function Write-RunState {
    param(
        [Parameter(Mandatory)][psobject]$State,
        [Parameter(Mandatory)][string]$Path,
        [string]$NewState,
        [string]$Stage,
        [hashtable]$Patch,
        [object]$ErrorObject
    )
    return Move-PQRunState -State $State -StatePath $Path -NewState $NewState -Stage $Stage -Patch $Patch -ErrorObject $ErrorObject
}

function Write-Heartbeat([string]$Path, [string]$Stage, [string]$State = 'running') {
    Write-PQJsonAtomic -Path $Path -Value ([ordered]@{
        schema_version = '1.0'
        state = $State
        stage = $Stage
        utc = [DateTime]::UtcNow.ToString('o')
    })
}

function Get-CacheSnapshot([string]$Path) {
    return Get-PQCacheSnapshot -Path $Path
}

function Assert-ExactCachePath([string]$Path) {
    $resolved = [System.IO.Path]::GetFullPath($Path)
    if (-not $resolved.Equals('C:\Users\Admin\.codex\models_cache.json', [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'provider_cache_path_mismatch'
    }
    Test-PQNoReparseComponents -Path $resolved | Out-Null
    return $resolved
}

function Assert-ExternalPath([string]$Path, [string]$ExternalRoot) {
    if ([string]::IsNullOrWhiteSpace($Path) -or [string]::IsNullOrWhiteSpace($ExternalRoot) -or
        $Path -match '(^|[\\/])\.\.([\\/]|$)') {
        throw 'provider_external_path_escape'
    }
    $root = [System.IO.Path]::GetFullPath($ExternalRoot).TrimEnd('\', '/') + '\'
    $resolved = [System.IO.Path]::GetFullPath($Path)
    if (-not $resolved.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw 'provider_external_path_escape'
    }
    Test-PQNoReparseComponents -Path $resolved | Out-Null
    return $resolved
}

function Get-SanitizedError([string]$Code, [string]$Stage, [string]$Reason) {
    return Get-PQSanitizedError -Code $Code -Stage $Stage -Reason $Reason
}

Export-ModuleMember -Function Get-Sha256,Write-JsonAtomic,New-InitialState,Write-RunState,Write-Heartbeat,Get-CacheSnapshot,Assert-ExactCachePath,Assert-ExternalPath,Get-SanitizedError
