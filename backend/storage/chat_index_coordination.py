"""Coordinate chat-index writes and deletion across local processes.

The caller must supply the app-owned runtime root. No user content is written to
the lock file. Operating-system locks are released automatically on process exit.
"""

from __future__ import annotations

from contextlib import contextmanager
import math
import os
from pathlib import Path
import threading
import time
from typing import Iterator


class ChatIndexLockError(RuntimeError):
    """The shared chat-index mutation lock could not be acquired safely."""


_registry_lock = threading.Lock()
_thread_locks: dict[str, threading.Lock] = {}


@contextmanager
def chat_index_guard(
    runtime_root: Path, *, timeout_seconds: float = 5.0
) -> Iterator[None]:
    """Acquire a bounded thread and OS lock for this app-owned runtime."""
    timeout = float(timeout_seconds)
    if not math.isfinite(timeout) or not 0 <= timeout <= 30:
        raise ValueError("chat_index_lock_timeout_invalid")
    root = Path(runtime_root).resolve()
    if not root.is_dir():
        raise ChatIndexLockError("chat_index_lock_unavailable")
    lock_path = root / "locks" / "chat-index.lock"
    with _registry_lock:
        thread_lock = _thread_locks.setdefault(str(lock_path), threading.Lock())
    deadline = time.monotonic() + timeout
    if not thread_lock.acquire(timeout=timeout):
        raise ChatIndexLockError("chat_index_lock_unavailable")
    stream = None
    locked = False
    try:
        try:
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            stream = lock_path.open("a+b")
            stream.seek(0, os.SEEK_END)
            if stream.tell() == 0:
                stream.write(b"\0")
                stream.flush()
            while not locked:
                try:
                    stream.seek(0)
                    if os.name == "nt":
                        import msvcrt

                        msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
                    else:
                        import fcntl

                        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    locked = True
                except OSError:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise ChatIndexLockError("chat_index_lock_unavailable") from None
                    time.sleep(min(0.05, remaining))
        except OSError as exc:
            raise ChatIndexLockError("chat_index_lock_unavailable") from exc
        yield
    finally:
        try:
            if stream is not None:
                try:
                    if locked:
                        stream.seek(0)
                        if os.name == "nt":
                            import msvcrt

                            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
                        else:
                            import fcntl

                            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
                finally:
                    stream.close()
        finally:
            thread_lock.release()
