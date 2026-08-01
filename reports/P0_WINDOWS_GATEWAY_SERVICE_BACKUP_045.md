# P0 Windows Gateway service backup 045

Private backup completed before any service-registration change.

| Field | Result |
| --- | --- |
| Backup id | `p0-045-20260726T111038Z` |
| Storage | existing private OpenClaw state root `backups` directory; outside Git |
| Files | Task XML, `gateway.cmd`, sanitized metadata, rollback instructions |
| Task XML SHA-256 | `0198D8A19785305C2D9CDA355FF0A50D9CE7B3E42CAE94E51B8ECBB34D50A94B` |
| Launcher SHA-256 | `D288BF7E7CA8759F48F81980C359E3E7D8847B1C4D76751CF3841131C2562B07` |
| Metadata SHA-256 | `11E7DEA5029E4BEB023BF056B381563810D8D68F1441CAA66A5C1F627E655B4F` |
| Task XML contains secret | false |
| Launcher contains secret | false |
| Pre-backup Gateway / Project Gateway | healthy / 0 processes |

The private metadata retains the current configuration path/SHA, Task name,
version, and rollback instructions. No raw service artifact was copied into the
repository.
