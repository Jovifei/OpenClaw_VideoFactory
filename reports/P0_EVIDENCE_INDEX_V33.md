# P0 Evidence Index V33

| Evidence | Result | Proof layer |
|---|---|---|
| `tests/test_media_action_ticket.py` | PASS | offline deterministic ticket contract |
| Full Python unittest discovery | PASS (298/298) | offline regression |
| Full Pester discovery | PASS (123/123) | offline PowerShell/static regression |
| `scripts/v28_schema_tests.py` | PASS | 88/88 schema checks |
| `.venv` `pip check` | PASS | dependency consistency |
| `git diff --check` | PASS | whitespace integrity |
| Scoped secret-pattern scan | PASS | source/report scan only |
| `P0_LIVE_MEDIA_R2_QUALIFICATION_012.md` | historical PASS | real ingress baseline, not R3-R5 |
| `P0_R3_TWO_MESSAGE_EVENT_20260720.md` | historical NOT_PASSED | preserved prior R3 failure |

V33 does not promote an offline, static, or historical result to a real media
qualification.
