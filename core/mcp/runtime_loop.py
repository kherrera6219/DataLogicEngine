"""Dedicated asyncio loop for durable stdio MCP client lifecycles."""

from __future__ import annotations

import asyncio
import concurrent.futures
import threading
from typing import Any, Coroutine


class MCPRuntimeLoop:
    """Own background readers for connector processes across Flask requests."""

    def __init__(self) -> None:
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread: threading.Thread | None = None
        self._ready = threading.Event()
        self._lock = threading.Lock()
        self._operations: dict[str, concurrent.futures.Future[Any]] = {}

    def _ensure_started(self) -> asyncio.AbstractEventLoop:
        with self._lock:
            if self._loop is not None and self._thread is not None and self._thread.is_alive():
                return self._loop
            self._ready.clear()
            self._thread = threading.Thread(
                target=self._run,
                name="dle-mcp-runtime",
                daemon=True,
            )
            self._thread.start()
        if not self._ready.wait(timeout=5):
            raise RuntimeError("mcp_runtime_loop_start_timeout")
        if self._loop is None:
            raise RuntimeError("mcp_runtime_loop_unavailable")
        return self._loop

    def _run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        self._ready.set()
        try:
            loop.run_forever()
        finally:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()
            self._loop = None

    def submit(
        self,
        coroutine: Coroutine[Any, Any, Any],
        *,
        timeout: float,
        operation_id: str | None = None,
    ) -> Any:
        loop = self._ensure_started()
        future = asyncio.run_coroutine_threadsafe(coroutine, loop)
        if operation_id:
            with self._lock:
                self._operations[operation_id] = future
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError as exc:
            future.cancel()
            raise TimeoutError("mcp_runtime_operation_timeout") from exc
        finally:
            if operation_id:
                with self._lock:
                    if self._operations.get(operation_id) is future:
                        self._operations.pop(operation_id, None)

    def cancel(self, operation_id: str) -> bool:
        """Cancel one named in-flight coroutine from another request thread."""
        with self._lock:
            future = self._operations.get(str(operation_id))
        if future is None or future.done():
            return False
        return future.cancel()

    def stop(self) -> None:
        with self._lock:
            loop = self._loop
            thread = self._thread
            self._thread = None
            operations = list(self._operations.values())
            self._operations.clear()
        for future in operations:
            future.cancel()
        if loop is not None and loop.is_running():
            loop.call_soon_threadsafe(loop.stop)
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=5)
