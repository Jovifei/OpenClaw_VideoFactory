# P0 Dependency Gate Fix 030A

## Result

`DEPENDENCY_GATE_READY`

The project virtual environment lacked the declared dependency required by `services/feishu_gateway/service.py`: `jsonschema.Draft202012Validator` and `RefResolver`. The root cause was an incomplete bootstrap manifest: no `pyproject.toml` or lock file exists, `requirements-bootstrap.txt` previously listed only PyYAML, and `00_package_check.ps1` checked only `yaml`.

030A adds the single direct requirement `jsonschema>=4.0,<5` and makes the package gate import both `yaml` and `jsonschema`. No global/system Python, OpenClaw environment/configuration, Binding, Agent, Cron, OAuth, model, Gateway lifecycle, Feishu, or RPC state was changed.

## Installation boundary

- Resolver download: project `.venv` pip into `E:\Claude_allow\Download\p0-030-jsonschema-20260723`.
- Installation: project `.venv` only, from that captured directory using `--no-index`.
- Source record: pip-resolved wheels captured locally before installation; the install did not reach a network index.
- Dependency health: `python -m pip check` returned `No broken requirements found.`

## Resolved wheels

| Package | Version | License | Wheel SHA-256 |
| --- | --- | --- | --- |
| jsonschema | 4.26.0 | MIT | `D489F15263B8D200F8387E64B4C3A75F06629559FB73DEB8FDFB525F2DAB50CE` |
| attrs | 26.1.0 | MIT | `C647AA4A12DFBAD9333CA4E71FE62DDC36F4E63B2D260A37A8B83D2F043AC309` |
| jsonschema-specifications | 2025.9.1 | MIT | `98802FEE3A11EE76ECACA44429FDA8A41BFF98B00A0F2838151B113F210CC6FE` |
| referencing | 0.37.0 | MIT | `381329A9F99628C9069361716891D34AD94AF76E461DCB0335825AECC7692231` |
| rpds-py | 2026.6.3 | MIT | `2C958BF94822E9290A40AAF2A822D4BC5C88099093E3948AD6C571ECA9272E5F` |
| typing-extensions | 4.16.0 | PSF-2.0 | `481CAA481374E813C1B176ADA14E97F1F67A4539CE9CFEB3F350D78D6370C2E8` |

## Verification

| Check | Result |
| --- | --- |
| `scripts/v28_schema_tests.py` | PASS, 88/88 |
| `python -m unittest discover -s tests -p 'test_*.py' -v` | PASS, 179/179 |
| `python -m pip check` | PASS |
| Gateway schema-dependent tests previously blocked at import | PASS in the full suite |

The schema script is stdlib-only; the full suite is the proof that the Gateway's actual `jsonschema` imports now resolve and its schema validation tests execute.
