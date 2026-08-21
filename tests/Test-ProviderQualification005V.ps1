$ErrorActionPreference = 'Stop'
$module = Join-Path $PSScriptRoot '..\scripts\lib\ProviderQualification.psm1'
Import-Module $module -Force -WarningAction SilentlyContinue
$entryScript = Join-Path $PSScriptRoot '..\scripts\provider_qualification.ps1'
. $entryScript -QualificationProfile '005V' -LoadOnly

function New-PQ005VTestBoundary {
    return [ordered]@{
        branch = 'codex/ai-director-video-factory-phase2-001'
        head = '76180a59ea662bdf168d88baaeb777d3e8eb59ef'
        index_empty = $true
        protected_dirty_sha256 = [ordered]@{
            'PROJECT_STATUS.yaml' = ('a' * 64)
            'reports/P0_ACCEPTANCE_MATRIX_V2.yaml' = ('b' * 64)
            'scripts/analysis_request.py' = ('c' * 64)
            'scripts/analyzer_mcp.py' = ('d' * 64)
            'scripts/mcp_ingest_attachment.py' = ('e' * 64)
            'scripts/media_action_ticket.py' = ('f' * 64)
        }
    }
}

function New-PQ005VReservedState {
    param([string]$RunId = ('session_005v_reservation_' + [Guid]::NewGuid().ToString('N')))
    $state = New-PQInitialState -Profile (Get-PQProfile -QualificationProfile '005V') -RunId $RunId
    $state.revision = 5
    $state.state = 'worker_started'
    $state.stage = 'worker_launch'
    $state.last_checkpoint = 'worker_started'
    $state.source_freeze_sha256 = ('a' * 64)
    $state.supervisor_pid = 1
    $state.supervisor_token_sha256 = ('b' * 64)
    $state.worker_generation = 1
    $state.worker_launch_count = 1
    $state.worker_pid = 0
    $state.worker_token_sha256 = ('c' * 64)
    $state.lease_id = ('d' * 32)
    $state.lease_expires_utc = '2030-01-01T00:00:00.0000000Z'
    Assert-PQStateSchemaTestContract -State $state | Out-Null
    return $state
}

Describe 'ProviderQualification 005V isolated profile' {
    It 'binds the fixed task, namespace and one-shot policy' {
        $profile = Get-PQProfile -QualificationProfile '005V'
        $profile.profile | Should Be '005V'
        $profile.task_id | Should Be 'AI-DIRECTOR-PHASE2-REAL-PROVIDER-QUALIFICATION-005V'
        $profile.schema_version | Should Be '1.1'
        $profile.external_root | Should Be 'E:\Claude_allow\Download\codex-provider-recovery-005v'
        $profile.fixture_directory | Should Be 'examples\ai_director_provider_qualification_005v'
        $profile.expected_topic_digest | Should Be '1224cb6eb1e538f6b33f25664d19c8c22469ddff8b972e81b10404e81fc915d5'
        $profile.output_name | Should Be 'pink_pig_modbus_ai_provider_005v.mp4'
        $profile.max_worker_generations | Should Be 1
        $profile.allow_rehearsal | Should Be $false
        $profile.start_closed | Should Be $false
    }

    It 'keeps historical profiles closed and rejects rehearsal for 005V' {
        (Get-PQProfile -QualificationProfile '005R').start_closed | Should Be $true
        (Get-PQProfile -QualificationProfile '005S').start_closed | Should Be $true
        (Get-PQProfile -QualificationProfile '005T').start_closed | Should Be $true
        (Get-PQProfile -QualificationProfile '005V').allow_rehearsal | Should Be $false
    }

    It 'keeps production schema validation free of a runtime test override' {
        $moduleSource = Get-Content -LiteralPath $module -Raw -Encoding UTF8
        $moduleSource | Should Not Match 'Set-PQStateSchemaTestValidator'
        $moduleSource | Should Not Match '\$script:PQStateSchemaTestValidator'
        $moduleSource | Should Match "throw 'provider_qualification_state_schema_validator_unavailable'"
    }

    It 'has no direct external command invocation in the U, U1, or V Pester files' {
        $forbidden = @('python', 'python.exe', 'py', 'py.exe', 'cmd', 'cmd.exe', 'powershell', 'powershell.exe', 'pwsh', 'pwsh.exe', 'start-process', 'invoke-expression')
        $testFiles = @(
            'Test-ProviderQualification005U.ps1',
            'Test-ProviderQualification005U1.ps1',
            'Test-ProviderQualification005V.ps1'
        )
        foreach ($file in $testFiles) {
            $tokens = $null
            $errors = $null
            $ast = [System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot $file), [ref]$tokens, [ref]$errors)
            @($errors).Count | Should Be 0
            $commandNames = @($ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.CommandAst] }, $true) | ForEach-Object {
                if ($_.CommandElements.Count -gt 0 -and $_.CommandElements[0] -is [System.Management.Automation.Language.StringConstantExpressionAst]) {
                    $_.CommandElements[0].Value.ToLowerInvariant()
                }
            })
            foreach ($name in $forbidden) {
                ($commandNames -contains $name) | Should Be $false
            }
            @($ast.FindAll({ param($node) $node -is [System.Management.Automation.Language.CommandAst] -and $node.InvocationOperator -eq [System.Management.Automation.Language.TokenKind]::Ampersand }, $true)).Count | Should Be 0
        }
    }

    It 'creates a schema-valid 005V reservation with worker pid zero' {
        $state = New-PQ005VReservedState -RunId 'session_005v_reservation'
        $state.worker_pid | Should Be 0
        { Assert-PQStateSchemaTestContract -State $state } | Should Not Throw
    }

    It 'rejects supervisor_ready with zero pid and a second generation' {
        $state = New-PQ005VReservedState -RunId 'session_005v_negative'
        $zeroReady = Copy-PQObject -Value $state
        $zeroReady.state = 'supervisor_ready'
        { Assert-PQStateSchemaTestContract -State $zeroReady } | Should Throw

        $secondGeneration = Copy-PQObject -Value $state
        $secondGeneration.worker_generation = 2
        $secondGeneration.worker_launch_count = 2
        { Assert-PQStateSchemaTestContract -State $secondGeneration } | Should Throw

        $reservedWithPid = Copy-PQObject -Value $state
        $reservedWithPid.worker_pid = 2
        { Assert-PQStateSchemaTestContract -State $reservedWithPid } | Should Throw
    }

    It 'keeps one-shot smoke and acceptance ledgers distinct from 005T' {
        (Get-PQCommandFingerprint -Name 'smoke' -TaskId 'AI-DIRECTOR-PHASE2-REAL-PROVIDER-QUALIFICATION-005V') | Should Not Be (Get-PQCommandFingerprint -Name 'smoke' -TaskId 'AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005T')
        (Get-PQCommandFingerprint -Name 'acceptance' -TaskId 'AI-DIRECTOR-PHASE2-REAL-PROVIDER-QUALIFICATION-005V') | Should Not Be (Get-PQCommandFingerprint -Name 'acceptance' -TaskId 'AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005T')
    }

    It 'returns stable BLOCKED_SUPERVISOR_DIED for an in-process false liveness probe' {
        $probeState = [pscustomobject]@{ calls = 0 }
        $probe = {
            $probeState.calls++
            return $false
        }.GetNewClosure()

        { Assert-PQSupervisorLivenessProbe -SupervisorLivenessProbe $probe } | Should Throw 'BLOCKED_SUPERVISOR_DIED'
        { Assert-PQSupervisorLivenessProbe -SupervisorLivenessProbe $probe } | Should Throw 'BLOCKED_SUPERVISOR_DIED'

        $probeState.calls | Should Be 2
        (Test-Path -LiteralPath (Join-Path $TestDrive 'command-continued.txt') -PathType Leaf) | Should Be $false
    }

    It 'routes Invoke-PQBoundedProcess through the pure Supervisor liveness guard' {
        $moduleSource = Get-Content -LiteralPath $module -Raw -Encoding UTF8
        $start = $moduleSource.IndexOf('function Invoke-PQBoundedProcess {', [System.StringComparison]::Ordinal)
        $end = $moduleSource.IndexOf('function Assert-PQManifestPath {', [System.StringComparison]::Ordinal)

        $start | Should BeGreaterThan -1
        $end | Should BeGreaterThan $start
        $moduleSource.Substring($start, $end - $start) | Should Match 'Assert-PQSupervisorLivenessProbe\s+-SupervisorLivenessProbe\s+\$SupervisorLivenessProbe'
    }

    It 'routes smoke, acceptance, media, and regression commands through the Supervisor liveness probe' {
        $scriptPath = Join-Path $PSScriptRoot '..\scripts\provider_qualification.ps1'
        $source = Get-Content -LiteralPath $scriptPath -Raw -Encoding UTF8
        foreach ($functionName in @('Invoke-PQSmoke', 'Invoke-PQAcceptance', 'Invoke-PQMediaVerification', 'Invoke-PQRegressionSuite')) {
            $start = $source.IndexOf(('function ' + $functionName + ' {'), [System.StringComparison]::Ordinal)
            $start | Should BeGreaterThan -1
            ($source.Substring($start)) | Should Match 'SupervisorLivenessProbe'
        }
    }

    It 'freezes the complete 005V Director production import closure and contracts' {
        $targets = @(Get-PQ005VProductionFreezeTargets)
        $required = @(
            'generate_video.py',
            'src/factory/director/__init__.py',
            'src/factory/director/asset_selector.py',
            'src/factory/director/context.py',
            'src/factory/director/director_contract.py',
            'src/factory/director/factual.py',
            'src/factory/director/script_planner.py',
            'src/factory/director/storyboard_assembler.py',
            'src/factory/assets/pink_pig/loader.py',
            'assets/pink_pig/pig01.png',
            'assets/pink_pig/pig02.png',
            'assets/pink_pig/pig03.png',
            'assets/pink_pig/pig04.png',
            'assets/pink_pig/pig05.png',
            'assets/pink_pig/signature.png',
            'assets/pink_pig/demo_music.wav',
            'assets/modbus_rtu_illustrations/01-master-slave.png',
            'assets/modbus_rtu_illustrations/02-frame-layout.png',
            'assets/modbus_rtu_illustrations/03-serial-parameters.png',
            'assets/modbus_rtu_illustrations/04-troubleshooting.png',
            'assets/modbus_rtu_illustrations/05-summary.png',
            'video_factory/pipeline/audio_planner.py',
            'video_factory/pipeline/composition.py',
            'video_factory/pipeline/failure_contract.py',
            'video_factory/pipeline/job_state.py',
            'video_factory/pipeline/pink_pig_quality.py',
            'video_factory/pipeline/renderer.py',
            'video_factory/pipeline/storyboard.py',
            'video_factory/pipeline/validation.py',
            'video_factory/pipeline/voice_generator.py',
            'video_factory/configs/director_job.defaults.yaml',
            'config/account.yaml',
            'config/account_columns.yaml',
            'config/topic_rules.yaml',
            'config/mascot_usage.yaml',
            'schemas/video/director_script.schema.json',
            'schemas/video/director_run_report.schema.json',
            'schemas/video/video_job.schema.json',
            'schemas/video/video_job_state.schema.json',
            'src/factory/assets/pink_pig/registry.schema.json',
            'skills/pink-pig-mascot-director/SKILL.md'
        )
        foreach ($relative in $required) {
            ($targets -contains $relative) | Should Be $true
        }
    }

    Context '005V fixture source-freeze' {
        It 'fails closed when the 005V fixture README is absent or hash-drifted' {
            $profile = Get-PQProfile -QualificationProfile '005V'
            $fixtureTargets = @(Get-PQFixtureFreezeTargets -QualificationProfile $profile -IncludeFixture)
            $fixtureTargets | Should Be @(
                'examples\ai_director_provider_qualification_005v/topic.txt',
                'examples\ai_director_provider_qualification_005v/factual_brief.json',
                'examples\ai_director_provider_qualification_005v/README.md'
            )

            $miniRepo = Join-Path $TestDrive 'fixture-repo'
            $entries = @()
            foreach ($relative in $fixtureTargets) {
                $path = Join-Path $miniRepo ($relative -replace '/', '\\')
                New-Item -ItemType Directory -Path (Split-Path -Parent $path) -Force | Out-Null
                Set-Content -LiteralPath $path -Value ('fixture:' + $relative) -Encoding UTF8
                $item = Get-Item -LiteralPath $path
                $entries += [pscustomobject]@{ path = $relative; bytes = [int64]$item.Length; sha256 = Get-PQSha256 -Path $path }
            }

            { Assert-PQFixtureFreezeEntries -Files $entries -QualificationProfile $profile -EvidenceRepoRoot $miniRepo -IncludeFixture } | Should Not Throw

            $missingReadme = @($entries | Where-Object { $_.path -ne 'examples\ai_director_provider_qualification_005v/README.md' })
            { Assert-PQFixtureFreezeEntries -Files $missingReadme -QualificationProfile $profile -EvidenceRepoRoot $miniRepo -IncludeFixture } | Should Throw 'provider_qualification_fixture_freeze_binding_invalid'

            ($entries | Where-Object { $_.path -eq 'examples\ai_director_provider_qualification_005v/README.md' }).sha256 = ('0' * 64)
            { Assert-PQFixtureFreezeEntries -Files $entries -QualificationProfile $profile -EvidenceRepoRoot $miniRepo -IncludeFixture } | Should Throw 'provider_qualification_fixture_freeze_drift'
        }
    }

    It 'hash-binds 005T immutable evidence with TestDrive fixtures and detects drift' {
        $fixtureRepo = Join-Path $TestDrive '005t-evidence-repo'
        foreach ($relative in Get-PQ005TImmutableEvidenceTargets) {
            $path = Join-Path $fixtureRepo ($relative -replace '/', '\\')
            New-Item -ItemType Directory -Path (Split-Path -Parent $path) -Force | Out-Null
            Set-Content -LiteralPath $path -Value ('fixture:' + $relative) -Encoding UTF8
        }
        $fixtureExternal = Join-Path $TestDrive '005t-evidence-external'
        $runId = 'session_20260811T175916Z_43092'
        $runRoot = Join-Path $fixtureExternal $runId
        New-Item -ItemType Directory -Path $runRoot -Force | Out-Null
        [ordered]@{
            task_id = 'AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005T'
            qualification_profile = '005T'
            run_id = $runId
        } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runRoot 'state.json') -Encoding UTF8
        $terminalPath = Join-Path $fixtureExternal ('.qualification.terminal.' + $runId + '.lock')
        [ordered]@{
            task_id = 'AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005T'
            qualification_profile = '005T'
            run_id = $runId
        } | ConvertTo-Json | Set-Content -LiteralPath $terminalPath -Encoding UTF8
        (Get-Item -LiteralPath $terminalPath -Force).IsReadOnly = $true

        $evidence = Get-PQ005TImmutableEvidenceFreeze -EvidenceRepoRoot $fixtureRepo -EvidenceExternalRoot $fixtureExternal -ExpectedRunId $runId
        $evidence.entries.Count | Should Be 8
        (@($evidence.entries.reference) -contains 'repo:reports/change_requests/AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005T.json') | Should Be $true
        (@($evidence.entries.reference) -contains ('005T-run:' + $runId + '/state.json')) | Should Be $true
        (@($evidence.entries.reference) -contains ('005T-terminal:' + $runId)) | Should Be $true
        { Assert-PQ005TImmutableEvidenceFreezeDocument -Evidence $evidence -EvidenceRepoRoot $fixtureRepo -EvidenceExternalRoot $fixtureExternal } | Should Not Throw
        { Get-PQ005TImmutableEvidenceFreeze -EvidenceRepoRoot $fixtureRepo -EvidenceExternalRoot $fixtureExternal -ExpectedRunId 'session_other' } | Should Throw 'provider_qualification_005t_immutable_evidence_invalid'

        $freeze = [ordered]@{ files = @(); immutable_005t_evidence = $evidence; sha256 = ('a' * 64) }
        $manifest = New-PQRunManifest -RunId 'session_005v_fixture' -RunRoot (Join-Path $TestDrive '005v-run') -Boundary ([ordered]@{}) -Freeze $freeze -SupervisorTokenHash ('b' * 64)
        $manifest.immutable_005t_evidence_sha256 | Should Be $evidence.sha256

        Set-Content -LiteralPath (Join-Path $fixtureRepo 'reports\CODEX_PROVIDER_DETACHED_RUN_005T.json') -Value 'tampered' -Encoding UTF8
        { Assert-PQ005TImmutableEvidenceFreezeDocument -Evidence $evidence -EvidenceRepoRoot $fixtureRepo -EvidenceExternalRoot $fixtureExternal } | Should Throw
    }

    It 'requires the canonical 005V Change Request status before operational modes' {
        $profile = Get-PQProfile -QualificationProfile '005V'
        $base = [pscustomobject]@{
            id = $profile.task_id
            does_not_authorize_oauth_profile_model_changes = $true
            does_not_authorize_commit_or_push = $true
            allow_rehearsal = $false
            execution_status = 'prepared_pending_contract_review'
        }
        { Assert-PQOperationalAuthorization -Profile $profile -ChangeRequest $base -Mode 'Preflight' } | Should Throw 'provider_qualification_change_request_not_authorized'
        $base.execution_status = 'contract_review_approved_pending_preflight'
        { Assert-PQOperationalAuthorization -Profile $profile -ChangeRequest $base -Mode 'Preflight' } | Should Not Throw
        { Assert-PQOperationalAuthorization -Profile $profile -ChangeRequest $base -Mode 'Start' } | Should Throw 'provider_qualification_change_request_not_authorized'
        $base.execution_status = 'ready_for_worker'
        { Assert-PQOperationalAuthorization -Profile $profile -ChangeRequest $base -Mode 'Start' } | Should Not Throw
        { Assert-PQOperationalAuthorization -Profile $profile -ChangeRequest $base -Mode 'Rehearse' } | Should Throw 'provider_qualification_rehearsal_not_authorized'
    }

    It 'keeps the historical CR blocked and recognizes only an explicit preflight bridge' {
        $old = Get-Content -Raw (Join-Path $PSScriptRoot '..\reports\change_requests\AI-DIRECTOR-PHASE2-PROVIDER-QUALIFICATION-005V.json') | ConvertFrom-Json
        $old.execution_status | Should Be 'baseline_blocked'
        $bridge = Get-Content -Raw (Join-Path $PSScriptRoot '..\reports\change_requests\AI-DIRECTOR-PHASE2-PROVIDER-PREFLIGHT-005V2.json') | ConvertFrom-Json
        $bridge.execution_status | Should Be 'preflight_blocked'
        $bridge.parent_profile_task_id | Should Be 'AI-DIRECTOR-PHASE2-REAL-PROVIDER-QUALIFICATION-005V'
        $bridge.maximum_preflight_commands | Should Be 1
        $bridge.maximum_worker_generations | Should Be 0
        $bridge.maximum_smoke_commands | Should Be 0
        $bridge.maximum_acceptance_commands | Should Be 0
        $bridge.does_not_authorize_worker_start | Should Be $true
        $bridge.does_not_authorize_provider_execution | Should Be $true
        $bridge.result.status | Should Be 'PREFLIGHT_BLOCKED'
        $bridge.result.exit_code | Should Be 1
        $bridge.result.smoke_attempts | Should Be 0
        $bridge.result.acceptance_attempts | Should Be 0
        $script = Get-Content -Raw (Join-Path $PSScriptRoot '..\scripts\provider_qualification.ps1')
        $script | Should Match 'Get-PQOperationalChangeRequest -Mode \$Mode'
        $script | Should Match 'source_freeze_sha256'
    }

    It 'uses safe schema-validation cleanup instead of recursive removal' {
        $safeRoot = Join-Path $TestDrive 'safe-validation'
        $safeTree = Join-Path $safeRoot '.qualification-schema-check'
        New-Item -ItemType Directory -Path (Join-Path $safeTree 'nested') -Force | Out-Null
        Set-Content -LiteralPath (Join-Path $safeTree 'nested\error.err') -Value 'test' -Encoding UTF8
        { Remove-PQSafeValidationDirectory -Path $safeTree -AllowedRoot $safeRoot } | Should Not Throw
        (Test-Path -LiteralPath $safeTree) | Should Be $false
        $source = Get-Content -Raw (Join-Path $PSScriptRoot '..\scripts\provider_qualification.ps1')
        $source | Should Not Match 'Remove-Item -LiteralPath \$validationRaw -Recurse'
    }

    It 'requires a canonical boundary digest and a run-bound independent review report' {
        $runRoot = Join-Path $TestDrive 'review-bindings'
        New-Item -ItemType Directory -Path $runRoot | Out-Null
        $manifest = [pscustomobject]@{
            task_id = 'AI-DIRECTOR-PHASE2-REAL-PROVIDER-QUALIFICATION-005V'
            qualification_profile = '005V'
            run_id = 'session_005v_review_binding'
            boundary = New-PQ005VTestBoundary
        }
        $reportPath = Join-Path $runRoot 'INDEPENDENT_FINAL_REVIEW_REPORT.json'
        $report = [ordered]@{
            task_id = $manifest.task_id
            profile = $manifest.qualification_profile
            run_id = $manifest.run_id
            reviewed_at_utc = '2030-01-01T00:00:00Z'
        }
        $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportPath -Encoding UTF8
        $review = [pscustomobject]@{
            boundary = Copy-PQObject -Value $manifest.boundary
            protected_boundary_sha256 = Get-PQCanonicalBoundarySha256 -Boundary $manifest.boundary
            review_report_file = 'INDEPENDENT_FINAL_REVIEW_REPORT.json'
            review_report_sha256 = Get-PQSha256 -Path $reportPath
        }

        { Assert-PQFinalReviewBindings -Review $review -Manifest $manifest -RunRoot $runRoot } | Should Not Throw

        $review.review_report_sha256 = ('a' * 64)
        { Assert-PQFinalReviewBindings -Review $review -Manifest $manifest -RunRoot $runRoot } | Should Throw
        $review.review_report_sha256 = Get-PQSha256 -Path $reportPath
        $review.protected_boundary_sha256 = ('b' * 64)
        { Assert-PQFinalReviewBindings -Review $review -Manifest $manifest -RunRoot $runRoot } | Should Throw

        foreach ($path in @(
            'PROJECT_STATUS.yaml',
            'reports/P0_ACCEPTANCE_MATRIX_V2.yaml',
            'scripts/analysis_request.py',
            'scripts/analyzer_mcp.py',
            'scripts/mcp_ingest_attachment.py',
            'scripts/media_action_ticket.py'
        )) {
            $review.boundary = New-PQ005VTestBoundary
            $review.boundary.protected_dirty_sha256[$path] = ('0' * 64)
            $review.protected_boundary_sha256 = Get-PQCanonicalBoundarySha256 -Boundary $manifest.boundary
            (Get-PQCanonicalBoundarySha256 -Boundary $review.boundary) | Should Not Be $review.protected_boundary_sha256
            { Assert-PQFinalReviewBindings -Review $review -Manifest $manifest -RunRoot $runRoot } | Should Throw 'provider_qualification_final_review_boundary_not_bound'
        }
    }

    It 'accepts only a hash-bound, run-bound explicit boundary evidence file' {
        $runRoot = Join-Path $TestDrive 'boundary-evidence'
        New-Item -ItemType Directory -Path $runRoot | Out-Null
        $manifest = [pscustomobject]@{
            task_id = 'AI-DIRECTOR-PHASE2-REAL-PROVIDER-QUALIFICATION-005V'
            qualification_profile = '005V'
            run_id = 'session_005v_boundary_evidence'
            boundary = New-PQ005VTestBoundary
        }
        $reportPath = Join-Path $runRoot 'INDEPENDENT_FINAL_REVIEW_REPORT.json'
        ([ordered]@{ task_id = $manifest.task_id; profile = $manifest.qualification_profile; run_id = $manifest.run_id } | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $reportPath -Encoding UTF8
        $evidencePath = Join-Path $runRoot 'FINAL_REVIEW_BOUNDARY_EVIDENCE.json'
        ([ordered]@{ task_id = $manifest.task_id; profile = $manifest.qualification_profile; run_id = $manifest.run_id; boundary = $manifest.boundary } | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $evidencePath -Encoding UTF8
        $review = [pscustomobject]@{
            boundary = Copy-PQObject -Value $manifest.boundary
            protected_boundary_sha256 = Get-PQSha256 -Path $evidencePath
            protected_boundary_evidence_file = 'FINAL_REVIEW_BOUNDARY_EVIDENCE.json'
            review_report_file = 'INDEPENDENT_FINAL_REVIEW_REPORT.json'
            review_report_sha256 = Get-PQSha256 -Path $reportPath
        }

        { Assert-PQFinalReviewBindings -Review $review -Manifest $manifest -RunRoot $runRoot } | Should Not Throw

        ([ordered]@{ task_id = $manifest.task_id; profile = $manifest.qualification_profile; run_id = 'session_other'; boundary = $manifest.boundary } | ConvertTo-Json -Depth 8) | Set-Content -LiteralPath $evidencePath -Encoding UTF8
        { Assert-PQFinalReviewBindings -Review $review -Manifest $manifest -RunRoot $runRoot } | Should Throw
    }

    It 'requires all six protected dirty hashes in final-review boundary evidence' {
        $schema = Get-Content -LiteralPath (Join-Path $PSScriptRoot '..\schemas\ops\provider_qualification_final_review.schema.json') -Raw -Encoding UTF8 | ConvertFrom-Json
        (@($schema.properties.boundary.required) -contains 'protected_dirty_sha256') | Should Be $true
        $hashes = $schema.properties.boundary.properties.protected_dirty_sha256
        @($hashes.required).Count | Should Be 6
        $boundary = New-PQ005VTestBoundary
        { Get-PQCanonicalBoundarySha256 -Boundary $boundary } | Should Not Throw
        $boundary.protected_dirty_sha256.'PROJECT_STATUS.yaml' = 'not-a-hash'
        { Get-PQCanonicalBoundarySha256 -Boundary $boundary } | Should Throw 'provider_qualification_final_review_boundary_invalid'
    }
}
