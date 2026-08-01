$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$py = Join-Path $repo 'scripts\v28_schema_tests.py'

Describe 'V2.8 video workflow schemas and fixtures (offline stdlib)' {
    It 'runs the V2.8 schema test suite and all checks pass' {
        & py $py 2>&1 | Out-Null
        $LASTEXITCODE | Should Be 0
    }
    It 'V28_SCHEMA_TESTS.json reports zero failures' {
        $r = Get-Content (Join-Path $repo 'reports\V28_SCHEMA_TESTS.json') -Raw | ConvertFrom-Json
        $r.failed | Should Be 0
        $r.total | Should BeGreaterThan 0
    }
    It 'all 17 schemas exist and parse' {
        $schemas = Get-ChildItem (Join-Path $repo 'schemas\video_workflow\*.schema.json')
        $schemas.Count | Should BeGreaterThan 16
        foreach ($s in $schemas) {
            { Get-Content $s.FullName -Raw | ConvertFrom-Json | Out-Null } | Should Not Throw
        }
    }
    It 'synthetic fixtures exist under tests/fixtures/workflow_v28' {
        $fx = Get-ChildItem (Join-Path $repo 'tests\fixtures\workflow_v28\*.json')
        $fx.Count | Should BeGreaterThan 14
    }
}
