# Single Consumer Runtime Proof 022

`scripts/migration/verify_consumer_state.py` evaluates an operator-supplied local observation. Its PASS condition is exactly one connection owner and no duplicate event identifier. It emits `consumer_count`, `connection_owner`, and `duplicate_risk`.

The script proves only the evaluation logic. It does not inspect production sockets or replace the required maintenance-window proof that the old core consumer exited before the project consumer connects.
