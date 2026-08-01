# P0 Single-Consumer Qualification

## Prepared local-only checks

| Script | Required local mock state | Pass condition |
| --- | --- | --- |
| `scripts/migration/pre_cutover_check.py --mock` | Old consumer=1, Project consumer=0, old WebSocket=1, Project WebSocket=0, backup/no pending work/no duplicates | Project Gateway is only a planned future owner |
| `scripts/migration/post_cutover_check.py --mock` | Old consumer=0, Project consumer=1, old WebSocket=0, Project WebSocket=1, owner=`project_gateway`, no duplicates | Exactly one supplied mock owner and one supplied mock socket |
| `scripts/migration/rollback_check.py --mock` | Failed Project start, Project stopped, old Binding restored, old text/attachment paths verified | Local rollback snapshot is internally complete |

All three scripts reject execution without `--mock`; they read only a supplied JSON snapshot and have no Binding, socket, process, or service-control code. The new qualification test exercises the passing pre/post snapshots and an overlap failure.

## Boundary against HIGH-025A-02

These checks prepare the observer evidence shape but do not inspect an authenticated long connection and do not implement an atomic fence. They cannot prove that an old Binding was stopped before Project startup. HIGH-025A-02 remains open for migration approval.

## Required real proof

An operator-authorized atomic/fenced ownership mechanism must be wired into old-Binding stop and Project start. An independent observer must then record exactly one authenticated owner, one WebSocket, and a duplicate-free event/reply stream.
