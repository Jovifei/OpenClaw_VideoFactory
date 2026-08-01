# Core Feishu Binding Control Contract 031

Status: `NOT_QUALIFIED`

| Required field | Contract result |
| --- | --- |
| STOP_METHOD | `NOT_QUALIFIED`. The reviewed account-routing command family contains configuration-mutating bind/unbind operations, but no target-specific, runtime-verified stop for the existing zhongshu Feishu consumer. It was not run. |
| VERIFY_STOPPED_METHOD | `NOT_QUALIFIED`. A future operator must provide three explicit sanitized observations to `verify_zhongshu_zero_consumer.py`; the current environment has no approved runtime collector. |
| RESTORE_METHOD | `NOT_QUALIFIED`. A candidate configuration rebind would require an approved pre-change manifest plus a verified Core restart/connection procedure. Neither is available. |
| VERIFY_RESTORED_METHOD | `NOT_QUALIFIED`. Requires a fresh explicit Core-owner observation followed by separately authorized text, attachment, and session checks. |
| RESTART_REQUIRED | `UNRESOLVED`. If configuration mutation is used, an entire Core Gateway restart may be needed to reapply channel routing; this has not been proven for zhongshu and must not be assumed. |
| EXPECTED_DOWNTIME_BOUNDARY | `UNBOUNDED / NOT QUALIFIED`. It cannot be bounded until stop, zero-consumer proof, restore, and restored-consumer proof are executable. |

`openclaw gateway stop` is an entire managed-service action, not a zhongshu Binding stop. It could affect unrelated channels and, with the binding still configured, cannot establish a durable handoff. It is not an approved substitute.

No Core Binding, Core Gateway, configuration, or restore action was executed.
