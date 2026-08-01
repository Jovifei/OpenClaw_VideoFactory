# Offline migration rehearsal

`experiments/feishu_gateway_migration/rehearsal.py` completed all five rehearsal steps with fake events only:

1. stop_core_binding
2. start_project_gateway
3. verify_one_consumer
4. route_fake_message
5. rollback_core_binding

The script writes the ordered step list as local evidence and performs no OpenClaw config change, no Gateway process action, no Feishu endpoint access, and no real credentials.
