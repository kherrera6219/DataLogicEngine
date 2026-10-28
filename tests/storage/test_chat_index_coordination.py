"""Chat-index mutation must coordinate across threads and processes."""

import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest

from backend.storage.chat_index_coordination import ChatIndexLockError, chat_index_guard


def test_chat_index_guard_rejects_concurrent_thread(tmp_path):
    def try_guard():
        with pytest.raises(ChatIndexLockError, match="chat_index_lock_unavailable"):
            with chat_index_guard(tmp_path, timeout_seconds=0.1):
                pass

    with chat_index_guard(tmp_path, timeout_seconds=1):
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(try_guard).result(timeout=5)
    with chat_index_guard(tmp_path, timeout_seconds=1):
        pass


def test_chat_index_guard_rejects_other_process(tmp_path):
    code = (
        "from pathlib import Path; "
        "from backend.storage.chat_index_coordination import chat_index_guard, ChatIndexLockError; "
        "import sys; "
        "guard = chat_index_guard(Path(sys.argv[1]), timeout_seconds=0.2); "
        "\ntry:\n with guard: pass\n"
        "except ChatIndexLockError: sys.exit(0)\n"
        "sys.exit(1)\n"
    )
    with chat_index_guard(tmp_path, timeout_seconds=1):
        result = subprocess.run(
            [sys.executable, "-c", code, str(tmp_path)],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    assert result.returncode == 0, result.stderr
