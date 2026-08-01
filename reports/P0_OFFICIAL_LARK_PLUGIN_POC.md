# Candidate A isolated PoC

`experiments/official-lark-plugin-replacement/test_contract.py` ran offline: 1/1 PASS. It proves the source has raw message/card registrations but fails the replacement precondition before plugin activation: no `preferOver` contract and a colliding `feishu` Channel ID. No dependency was installed and no plugin was loaded, so no second WebSocket consumer could be created.

Candidate A is closed with `OFFICIAL_PLUGIN_CANNOT_REPLACE_CORE_CHANNEL`; this is a source/contract failure, not a Feishu live test.
