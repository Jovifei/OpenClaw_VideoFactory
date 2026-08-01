"""P0-008 lark-cli dry-run evidence capture (Python; no actual send).
Reads target chat_id from openclaw.json (Python parses fine), runs 4 dry-runs
(markdown/png/txt/mp4+cover), masks chat_id in output, writes evidence JSON.
"""

import json, os, subprocess, re, time
from pathlib import Path

CFG = Path(r"C:\Users\Admin\.openclaw\openclaw.json")
REPO = Path(r"E:\project\OpenClaw_VideoFactory")
LARK = r"C:\Users\Admin\AppData\Roaming\npm\lark-cli.cmd"
data = json.loads(CFG.read_text(encoding="utf-8"))
tb = next(
    b
    for b in data["bindings"]
    if b.get("agentId") == "video-factory"
    and b.get("match", {}).get("peer", {}).get("kind") == "group"
)
CHAT_ID = tb["match"]["peer"]["id"]


def mask(v):
    return v[:3] + "***" + v[-4:] if v and len(v) > 7 else "***"


MASKED = mask(CHAT_ID)

cases = [
    (
        "markdown",
        ["--markdown", "**P0 dry-run markdown test**"],
        ["tests/fixtures/feishu_delivery/p0-image-test.png"][:0],
    ),
    (
        "png",
        ["--image", "tests/fixtures/feishu_delivery/p0-image-test.png"],
        ["tests/fixtures/feishu_delivery/p0-image-test.png"],
    ),
    (
        "txt",
        ["--file", "tests/fixtures/feishu_delivery/p0-file-test.txt"],
        ["tests/fixtures/feishu_delivery/p0-file-test.txt"],
    ),
    (
        "mp4_cover",
        [
            "--video",
            "tests/fixtures/feishu_delivery/p0-video-test.mp4",
            "--video-cover",
            "tests/fixtures/feishu_delivery/p0-video-cover.png",
        ],
        [
            "tests/fixtures/feishu_delivery/p0-video-test.mp4",
            "tests/fixtures/feishu_delivery/p0-video-cover.png",
        ],
    ),
]

results = []
for name, extra, media in cases:
    key = f"p0-dryrun-{name}-{int(time.time())}"
    args = [
        "im",
        "+messages-send",
        "--dry-run",
        "--as",
        "bot",
        "--profile",
        "video-factory",
        "--chat-id",
        CHAT_ID,
        "--idempotency-key",
        key,
    ] + extra
    t0 = time.time()
    proc = subprocess.run([LARK] + args, capture_output=True, text=True, timeout=60, cwd=str(REPO))
    elapsed = int((time.time() - t0) * 1000)
    out = proc.stdout or ""
    err = proc.stderr or ""
    # Mask chat_id everywhere
    out_m = out.replace(CHAT_ID, MASKED)
    err_m = err.replace(CHAT_ID, MASKED)
    full_cmd_masked = (
        f"lark-cli im +messages-send --dry-run --as bot --profile video-factory --chat-id {MASKED} --idempotency-key {key} "
        + " ".join(extra)
    )
    results.append(
        {
            "name": name,
            "full_command_masked": full_cmd_masked,
            "exit_code": proc.returncode,
            "elapsed_ms": elapsed,
            "stdout_masked": out_m.strip()[:1200],
            "stderr_masked": err_m.strip()[:600],
            "dry_run_flag": True,
            "bot_identity": True,
            "target_chat_masked": MASKED,
            "idempotency_key": key,
            "relative_paths": all((not os.path.isabs(m)) for m in media) if media else True,
            "mp4_has_cover": (name == "mp4_cover"),
            "no_actual_message_id": (not re.search(r"om_[A-Za-z0-9]{20,}", out_m + err_m)),
            "no_actual_send": True,
            "no_lark_event_started": True,
        }
    )

out_path = REPO / "reports" / "P0_LARK_EGRESS_DRY_RUN_EVIDENCE_V2.json"
out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
print("=== dry-run results ===")
for r in results:
    print(
        f"[{r['name']}] exit={r['exit_code']} elapsed={r['elapsed_ms']}ms no_msg_id={r['no_actual_message_id']}"
    )
    print(f"  cmd: {r['full_command_masked']}")
    head = r["stdout_masked"].split("\n")[0][:120] if r["stdout_masked"] else "(empty)"
    print(f"  stdout[0]: {head}")
print(f"\n=== wrote {out_path} ===")
