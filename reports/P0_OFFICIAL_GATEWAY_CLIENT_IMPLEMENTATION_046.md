# Official Gateway Client Implementation 046

The Project bridge is implemented in `services/feishu_gateway/openclaw_rpc_official/` and is deliberately separate from the historical shared-token adapter.

| Control | Implementation |
|---|---|
| Project identity | `project-feishu-gateway`; generated only by the official client after explicit pairing authorization |
| Identity algorithm | official Ed25519 device identity and challenge signature |
| Initial privilege | `operator.read` only |
| Shared Gateway token | removed from the short-lived bridge child environment; never supplied to the official client |
| State location | `C:\Users\Admin\.openclaw-video-factory\device`, outside the repository |
| State protection | protected DACL with one ACE for the current Windows SID; inheritance protected |
| Python boundary | local stdio IPC with a random one-shot session secret; Python never reads device identity or token files |
| Active RPC methods | health only; the documented future methods fail closed as `bridge_method_not_active` |

The production-preflight runtime now uses the device-auth probe by default. The old shared-token entrypoint remains disabled and cannot be selected as the normal runtime path.

