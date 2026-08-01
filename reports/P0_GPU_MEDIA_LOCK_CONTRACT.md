# P0 GPU Media Lock Contract

Task: `P0-SINGLE-GROUP-MEDIA-ROUTER-007`
Implementation: `scripts/gpu_media_lock.py` (zero-dependency Python stdlib)
Status: **implemented and smoke-tested**

## Goal

Single-machine mutual exclusion for GPU-heavy media analysis on the RTX 4070 SUPER (12 GB VRAM). GPU heavy tasks must run with concurrency 1. Ingest is never blocked by GPU work: the lock is acquired only after a quarantine receipt exists, never before or during `ingest_attachment`.

## Scope

| Activity | Needs GPU lock? |
| --- | --- |
| `ingest_attachment` (copy + hash + receipt) | **No** (CPU + disk only) |
| `ffprobe` metadata probe | **No** (CPU) |
| ffmpeg bounded key-frame extraction (CPU) | **No** (CPU path) |
| faster-whisper CUDA transcription | **Yes** |
| VLM / multimodal image understanding | **Yes** |
| ComfyUI render | **Yes** (shares the same lock namespace) |

The lock is a single shared namespace `gpu-media` by default; analyzers MAY use finer names (`whisper`, `vlm`, `comfy`) but the contract is that no two GPU-heavy holders run at once. For 007 the default is a single `gpu-media` lock (concurrency 1) to keep the contract simple; a finer-grained split can be added later without changing the API.

## Lock record

Each lock file (`state/gpu_locks/<name>.lock`) contains:

```json
{
  "lock_name": "gpu-media",
  "job_id": "job_...",
  "message_id": "om_...",
  "attachment_index": 0,
  "pid": 12345,
  "started_at": "2026-07-18T01:04:52.710Z",
  "started_at_epoch": 1784209892.71,
  "heartbeat_at": "2026-07-18T01:05:12.003Z",
  "heartbeat_at_epoch": 1784209912.003,
  "timeout_seconds": 300.0,
  "stale_after_seconds": 120.0
}
```

## Semantics

- **Acquire**: atomic create via `os.open(O_CREAT|O_EXCL)`. If the file exists, check the holder:
  - if the holder PID is dead (OpenProcess + GetExitCodeProcess STILL_ACTIVE on Windows; `os.kill(pid,0)` on POSIX) -> reclaim;
  - else if `now - heartbeat_at > stale_after_seconds` -> reclaim;
  - else -> `GpuLockUnavailable` (or wait up to `wait_seconds` polling).
- **Heartbeat**: rewrite the lock file with a fresh `heartbeat_at` (temp + `os.replace`). Long GPU jobs must call `heartbeat()` at least every `stale_after_seconds` (default 120 s).
- **Release**: unlink the lock file.
- **Stale recovery**: a crashed holder leaves a lock that the next acquire reclaims after `stale_after_seconds` (or immediately if the PID is confirmed dead).
- **Crash release**: a holder that crashes stops heartbeating; the lock becomes stale and is reclaimed. There is no leaked permanent lock.
- **No new dependencies**: stdlib only (`os`, `json`, `time`, `ctypes` on Windows).

## Default tunables

| Parameter | Default | Note |
| --- | --- | --- |
| `timeout_seconds` | 300 | advisory; a holder may run longer if it heartbeats |
| `stale_after_seconds` | 120 | reclaim threshold |
| `wait_seconds` (acquire) | 0 | fail-fast by default; analyzers may pass `wait_seconds` to queue |
| lock dir | `state/gpu_locks/` (env `OPENCLAW_GPU_LOCK_DIR`) | project-local |

## Failure codes

- `gpu_lock_unavailable` - lock held by a live holder and `wait_seconds` exhausted.
- (Stale locks are reclaimed silently; they do not surface as a failure to the caller.)

## Smoke results (2026-07-18)

- acquire -> `held=true, pid_alive=true`
- second acquire while held -> `acquired=false, error=gpu_lock_unavailable`, exit 2
- `probe-stale` on a fresh live lock -> `stale=false`
- release -> `held=false`
- stale recovery (dead PID) -> reclaimed on next acquire

## Usage

```python
from gpu_media_lock import GpuMediaLock, GpuLockUnavailable
lock = GpuMediaLock.acquire("gpu-media", job_id="j1", message_id="om_x",
                            attachment_index=0, timeout_seconds=300)
try:
    ... CUDA work ...
    lock.heartbeat()
finally:
    lock.release()
```

CLI (for tests and ops):
```
python scripts/gpu_media_lock.py acquire gpu-media --job-id ... --message-id ... --attachment-index ...
python scripts/gpu_media_lock.py status gpu-media
python scripts/gpu_media_lock.py probe-stale gpu-media
python scripts/gpu_media_lock.py release gpu-media
```

## Invariants

- The lock is acquired only AFTER `ingest_attachment` returns a valid receipt (`content_parsed=false`, `quarantined=true`). Ingest is never gated by GPU availability.
- ffprobe and CPU frame extraction do not take the lock, so video analysis can probe container metadata and extract frames while a transcription is queued.
- ComfyUI tasks share the same lock namespace so media analysis and rendering never contend for VRAM simultaneously.
