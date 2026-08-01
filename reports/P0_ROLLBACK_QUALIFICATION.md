# P0 Rollback Qualification

## Scenario

`MOCK_ONLY: gateway_start_failure`

| Time | Simulated command label | Result |
| --- | --- | --- |
| T+0 | `SIMULATED project_gateway_start` | failed |
| T+5 | `SIMULATED project_gateway_exit_check` | confirmed stopped |
| T+20 | `SIMULATED restore_old_binding` | restored |
| T+40 | `SIMULATED old_path_text_attachment_check` | passed |

The local experiment records a recovery point of `old_binding_text_and_attachment_paths`, a modeled recovery time of 40 seconds, and a 60-second modeled objective. `commands_executed=false`: no process, Gateway, Binding, or configuration command was issued.

The rollback snapshot check passed in `tests.test_gateway_qualification_026`.

## Boundary against HIGH-025A-04

This is a deterministic failure model, not a measured service restoration. It provides no message-loss boundary, drain proof, state transaction/recovery proof, or real RTO/RPO. HIGH-025A-04 remains open for migration approval until a separately authorized controlled-channel rehearsal measures those controls.
