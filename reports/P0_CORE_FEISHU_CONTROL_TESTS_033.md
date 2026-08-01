# P0 Core Feishu Control Tests 033

The offline test set covers:

1. origin manifest and runtime-entry hashes;
2. real Shadow plugin visibility and Gateway readiness;
3. account-scoped start, repeated start, stop, repeated stop, restart after
   stop, final stop, and secondary-account isolation;
4. loopback-only transport, zero unexpected network access, connection close
   balance, and duplicate-connection rejection;
5. fail-closed preflight/postcheck/rollback scripts and their rejected
   `--execute` path.

Final command evidence (fresh run bound at 00:40:16 Asia/Shanghai):

- `python experiments/core_feishu_control_contract/shadow_lifecycle_probe.py`:
  exit `0`; Gateway ready, 34 guard records, 2 Gateway records, external
  access `0`, fake SDK `2/2`, active `0`.
- `python -m unittest tests/test_core_feishu_plugin_lifecycle_033.py`:
  expected offline suite; no production endpoint.
- `preflight.py` and `postcheck.py` against the fresh result: `PASS`, exit
  `0`; `--execute`: `BLOCKED`, exit `2`.

No test sends Feishu traffic or invokes a production Gateway.
