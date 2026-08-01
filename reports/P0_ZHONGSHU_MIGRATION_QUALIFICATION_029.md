# P0 Zhongshu Migration Qualification 029

## Result

Preparation status: `ZHONGSHU_MIGRATION_READY`.

Execution status: `ZHONGSHU_MIGRATION_WAITING_AUTH`.

029 replaces the obsolete separate-test-App assumption with the existing `zhongshu` entrance as the only future migration target. This result certifies only the preparation assets and their local behavior. It is not evidence of a live cutover, a Feishu connection, an OpenClaw RPC call, a Binding change, Gateway lifecycle action, or message delivery.

## Delivered controls

- `P0_ZHONGSHU_MIGRATION_PLAN_029.md` defines T-30 through T+15, including an exclusive Core-to-Project consumer handoff.
- `P0_ZHONGSHU_ROLLBACK_PLAN_029.md` requires Project=0 before Core restoration and Core=1/Project=0 after restoration.
- `zhongshu_preflight.py` accepts only a sanitized read-only snapshot and requires Core=1, Project=0, combined=1, no active work, a backup manifest, and the rollback plan.
- `zhongshu_postcheck.py` accepts only sanitized read-only snapshots and requires Core=0, Project=1, combined=1, unique delivery hashes, and preserved session lineage.
- Both scripts have no network, OpenClaw, Feishu, subprocess, process-control, message-send, or configuration-write capability.

## Local verification

| Check | Result |
| --- | --- |
| `py_compile` for both scripts and their unit test | PASS |
| `python -m unittest discover -s tests -p 'test_*migration*.py' -v` | PASS, 10/10 |
| 029 change request JSON parse | PASS |
| Required 029 artifacts | PASS, 7/7 before this evidence report |
| Credential-pattern candidate scan of 029 artifacts | PASS, 0 |

The broader Python suite is not reclassified by this report. Its pre-existing `jsonschema` virtual-environment dependency failure remains outside the authorized 029 migration-preparation scope.

## Artifact integrity

| Artifact | SHA-256 |
| --- | --- |
| Migration plan | `3EB90F9DFDC4EFEC4DFCBB16CD1CB74FC876B7A9C78006E189C85CB45050E446` |
| Rollback plan | `9E5EE1A46035D04FD35056DF94E9C7DB51029BAAB67733A7FDC7FE24EE0D3863` |
| Authorization checklist | `8B63E6850F6882FE9A57D31326BF36E177457EDDADEC627328E5948CFB447DC5` |
| Change request | `A9D847C7F8A8C6A8298A274EA61C832FA9018E4A6CB55EC7887697A55B2BC1D0` |
| Preflight script | `9F6ABAF4B743B54C83B660F771851460D49B4155F02C962CFE6DA77F960A4A60` |
| Postcheck script | `531267FD758180771D45DEEB0050DB5F474513285C3B98923AFF93F3F7177A35` |
| Unit test | `A92B59ADD4183398F62BCC2773D50F13BDFD753FE59D1671F9CB99D8D05800F5` |

## Stop boundary

No authorization has been granted for the six actions in `P0_ZHONGSHU_MIGRATION_AUTHORIZATION.md`. Do not execute a cutover until every box is explicitly approved for one maintenance window and a fresh operator-captured preflight snapshot passes.
