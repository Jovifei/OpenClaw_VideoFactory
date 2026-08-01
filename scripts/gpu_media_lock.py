"""
GPU Media Lock - single-machine mutual exclusion for GPU-heavy media analysis.

Zero-dependency (Python stdlib only). Windows-compatible.

Contract (P0_GPU_MEDIA_LOCK_CONTRACT.md):
  - GPU heavy tasks (faster-whisper CUDA, VLM, ComfyUI) concurrency = 1.
  - ffprobe / CPU frame extraction do NOT need this lock.
  - Lock record carries: lock_name, job_id, message_id, attachment_index,
    pid, started_at, heartbeat_at, timeout_seconds, stale_after_seconds.
  - Stale lock recovery: if the holder PID is dead OR heartbeat is older than
    stale_after_seconds, the lock is reclaimed.
  - Crash release: a crashed holder leaves a stale lock that the next acquire
    reclaims after stale_after_seconds (or immediately if PID is confirmed dead).
  - No new dependencies.

Usage (module):
    from gpu_media_lock import GpuMediaLock, GpuLockUnavailable
    lock = GpuMediaLock.acquire("whisper", job_id="j1", message_id="om_x",
                                 attachment_index=0, timeout_seconds=300)
    try:
        ... gpu work ...
        lock.heartbeat()
    finally:
        lock.release()

CLI (for tests):
    python scripts/gpu_media_lock.py acquire <name> --job-id ... --message-id ... --attachment-index ...
    python scripts/gpu_media_lock.py release <name>
    python scripts/gpu_media_lock.py status <name>
    python scripts/gpu_media_lock.py probe-stale <name>
"""

from __future__ import annotations

import json
import os
import sys
import time
import argparse
from pathlib import Path
from typing import Optional, Dict, Any


DEFAULT_LOCK_DIR = Path(
    os.environ.get(
        "OPENCLAW_GPU_LOCK_DIR",
        str(Path(__file__).resolve().parent.parent / "state" / "gpu_locks"),
    )
)


class GpuLockUnavailable(Exception):
    """Raised when a GPU lock cannot be acquired (held by a live holder)."""


def _pid_alive(pid: int) -> bool:
    """Return True if a process with `pid` is currently running on this host.

    Uses only stdlib. On Windows uses ctypes (kernel32 OpenProcess +
    GetExitCodeProcess STILL_ACTIVE); on POSIX uses os.kill(pid, 0).
    """
    if pid <= 0:
        return False
    try:
        if os.name == "nt":
            import ctypes

            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not handle:
                return False
            try:
                code = ctypes.c_ulong()
                if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                    return False
                return code.value == STILL_ACTIVE
            finally:
                kernel32.CloseHandle(handle)
        else:
            os.kill(pid, 0)
            return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but not ours; treat as alive (conservative).
        return True
    except Exception:
        return False


def _now_iso() -> str:
    import datetime

    return (
        datetime.datetime.fromtimestamp(time.time(), datetime.timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S."
        )
        + f"{int((time.time() % 1) * 1000):03d}Z"
    )


class GpuMediaLock:
    """File-based GPU mutex with PID + heartbeat + stale recovery."""

    def __init__(self, lock_path: Path, record: Dict[str, Any]):
        self.lock_path = lock_path
        self.record = record

    @property
    def name(self) -> str:
        return self.record.get("lock_name", self.lock_path.stem)

    @classmethod
    def _lock_path(cls, lock_name: str, lock_dir: Optional[Path] = None) -> Path:
        d = lock_dir or DEFAULT_LOCK_DIR
        d.mkdir(parents=True, exist_ok=True)
        safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in lock_name)
        return d / f"{safe}.lock"

    @classmethod
    def read(cls, lock_name: str, lock_dir: Optional[Path] = None) -> Optional["GpuMediaLock"]:
        p = cls._lock_path(lock_name, lock_dir)
        if not p.exists():
            return None
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
        return cls(p, rec)

    @classmethod
    def is_stale(
        cls, lock_name: str, stale_after: float = 120.0, lock_dir: Optional[Path] = None
    ) -> bool:
        existing = cls.read(lock_name, lock_dir)
        if existing is None:
            return False  # nothing to reclaim
        rec = existing.record
        pid = int(rec.get("pid", 0))
        hb = float(rec.get("heartbeat_at_epoch", 0))
        if not _pid_alive(pid):
            return True
        if (time.time() - hb) > stale_after:
            return True
        return False

    @classmethod
    def acquire(
        cls,
        lock_name: str,
        *,
        job_id: str,
        message_id: str,
        attachment_index: int,
        timeout_seconds: float = 300.0,
        stale_after_seconds: Optional[float] = None,
        wait_seconds: float = 0.0,
        poll_interval: float = 0.5,
        lock_dir: Optional[Path] = None,
    ) -> "GpuMediaLock":
        # Default leases cannot expire before their declared work window.
        # Explicit lower values remain available only to isolated lock tests.
        if stale_after_seconds is None:
            stale_after_seconds = max(float(timeout_seconds) + 30.0, 120.0)
        else:
            stale_after_seconds = float(stale_after_seconds)
        p = cls._lock_path(lock_name, lock_dir)
        deadline = time.time() + wait_seconds
        while True:
            # Reclaim stale locks first.
            existing = cls.read(lock_name, lock_dir)
            if existing is not None:
                rec = existing.record
                pid = int(rec.get("pid", 0))
                hb = float(rec.get("heartbeat_at_epoch", 0))
                stale = (not _pid_alive(pid)) or ((time.time() - hb) > stale_after_seconds)
                if stale:
                    try:
                        existing.lock_path.unlink()
                    except FileNotFoundError:
                        pass
                else:
                    # Held by a live holder.
                    if time.time() > deadline:
                        raise GpuLockUnavailable(
                            f"GPU lock '{lock_name}' held by pid={pid} "
                            f"job={rec.get('job_id')} since {rec.get('started_at')}"
                        )
                    time.sleep(poll_interval)
                    continue
            # Atomic create with O_EXCL.
            try:
                fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            except FileExistsError:
                if time.time() > deadline:
                    raise GpuLockUnavailable(f"GPU lock '{lock_name}' file exists and is not stale")
                time.sleep(poll_interval)
                continue
            rec = {
                "lock_name": lock_name,
                "job_id": job_id,
                "message_id": message_id,
                "attachment_index": attachment_index,
                "pid": os.getpid(),
                "started_at": _now_iso(),
                "started_at_epoch": time.time(),
                "heartbeat_at": _now_iso(),
                "heartbeat_at_epoch": time.time(),
                "timeout_seconds": timeout_seconds,
                "stale_after_seconds": stale_after_seconds,
            }
            os.write(fd, json.dumps(rec, indent=2).encode("utf-8"))
            os.close(fd)
            return cls(p, rec)

    def heartbeat(self) -> None:
        """Refresh the heartbeat timestamp. No-op if lock was lost."""
        if not self.lock_path.exists():
            raise GpuLockUnavailable(f"lock {self.name} no longer exists; cannot heartbeat")
        self.record["heartbeat_at"] = _now_iso()
        self.record["heartbeat_at_epoch"] = time.time()
        # Atomic-ish: write temp then replace.
        tmp = self.lock_path.with_suffix(".lock.tmp")
        tmp.write_text(json.dumps(self.record, indent=2), encoding="utf-8")
        os.replace(tmp, self.lock_path)

    def release(self) -> bool:
        try:
            self.lock_path.unlink()
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False

    def status(self) -> Dict[str, Any]:
        alive = _pid_alive(int(self.record.get("pid", 0)))
        return {
            "lock_name": self.name,
            "held": True,
            "pid": self.record.get("pid"),
            "pid_alive": alive,
            "job_id": self.record.get("job_id"),
            "message_id": self.record.get("message_id"),
            "attachment_index": self.record.get("attachment_index"),
            "started_at": self.record.get("started_at"),
            "heartbeat_at": self.record.get("heartbeat_at"),
            "heartbeat_age_seconds": round(
                time.time() - float(self.record.get("heartbeat_at_epoch", 0)), 2
            ),
            "stale_after_seconds": self.record.get("stale_after_seconds"),
        }


def _cli():
    ap = argparse.ArgumentParser(description="GPU media lock (zero-dep)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("acquire")
    a.add_argument("name")
    a.add_argument("--job-id", required=True)
    a.add_argument("--message-id", required=True)
    a.add_argument("--attachment-index", type=int, required=True)
    a.add_argument("--timeout-seconds", type=float, default=300.0)
    a.add_argument("--stale-after-seconds", type=float, default=120.0)
    a.add_argument(
        "--hold-seconds",
        type=float,
        default=0.0,
        help="if >0, acquire then sleep then release (smoke)",
    )
    r = sub.add_parser("release")
    r.add_argument("name")
    s = sub.add_parser("status")
    s.add_argument("name")
    ps = sub.add_parser("probe-stale")
    ps.add_argument("name")
    ps.add_argument("--stale-after-seconds", type=float, default=120.0)
    args = ap.parse_args()

    if args.cmd == "acquire":
        try:
            lock = GpuMediaLock.acquire(
                args.name,
                job_id=args.job_id,
                message_id=args.message_id,
                attachment_index=args.attachment_index,
                timeout_seconds=args.timeout_seconds,
                stale_after_seconds=args.stale_after_seconds,
            )
            print(json.dumps({"acquired": True, **lock.status()}, indent=2))
            if args.hold_seconds > 0:
                time.sleep(args.hold_seconds)
                lock.heartbeat()
                lock.release()
                print(json.dumps({"released": True, "name": args.name}))
        except GpuLockUnavailable as e:
            print(
                json.dumps({"acquired": False, "error": "gpu_lock_unavailable", "message": str(e)})
            )
            sys.exit(2)
    elif args.cmd == "release":
        ok = GpuMediaLock(
            args.name and (DEFAULT_LOCK_DIR / f"{args.name}.lock"), {"lock_name": args.name}
        ).release()
        print(json.dumps({"released": ok, "name": args.name}))
    elif args.cmd == "status":
        lock = GpuMediaLock.read(args.name)
        if lock is None:
            print(json.dumps({"lock_name": args.name, "held": False}))
        else:
            print(json.dumps(lock.status(), indent=2))
    elif args.cmd == "probe-stale":
        stale = GpuMediaLock.is_stale(args.name, stale_after=args.stale_after_seconds)
        print(json.dumps({"lock_name": args.name, "stale": stale}))


if __name__ == "__main__":
    _cli()
