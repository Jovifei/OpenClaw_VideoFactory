# Feishu SDK Compatibility (020)

Recommended isolated dependency: `lark-oapi==1.7.1` (MIT, Python >=3.8). The official package imported successfully in an isolated Python 3.14.2 venv with `pip check` clean. It exposes event dispatch, WebSocket, and card-action handler surfaces.

OpenClaw compatibility is adapter-level only: this project calls documented Gateway RPC and does not load the SDK into OpenClaw or modify core source. No production compatibility claim is made until a maintenance-window mock transport and operator-controlled cutover verify the actual RPC endpoint.

Install/rollback: download wheels to `E:\Claude_allow\Download\p0_feishu_gateway_sdk_020`, create `experiments/feishu_gateway_sdk_test_env`, then install with `--no-index --find-links`. Roll back by removing only that isolated venv and its allowed download bundle; do not alter the production Python environment.
