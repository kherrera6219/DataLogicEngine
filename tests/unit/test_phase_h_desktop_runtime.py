import os

from backend.desktop.offline_queue import enqueue_chat_request, list_queue, mark_item
from backend.llm_gateway.gateway import NetworkState
from backend.storage.database_manager import DatabaseLifecycleManager
from backend.storage.runtime_settings import (
    get_local_slm_audit_mode,
    get_offline_queue_enabled,
    set_local_slm_audit_mode,
    set_offline_queue_enabled,
)


def test_database_manager_prefers_app_owned_jre(tmp_path, monkeypatch):
    bundled_java = tmp_path / "jre" / "bin" / ("java.exe" if os.name == "nt" else "java")
    bundled_java.parent.mkdir(parents=True)
    bundled_java.write_text("", encoding="utf-8")
    system_java = tmp_path / "system-java"
    monkeypatch.setenv("JAVA_HOME", str(system_java))

    manager = DatabaseLifecycleManager(base_dir=str(tmp_path))

    assert manager._find_java_home() == str(tmp_path / "jre")


def test_network_state_reports_local_model_online(monkeypatch):
    NetworkState._last_checked = None
    NetworkState._last_result = {}
    for env_name in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "AZURE_OPENAI_API_KEY"]:
        monkeypatch.delenv(env_name, raising=False)
    monkeypatch.setattr(NetworkState, "_tcp_reachable", staticmethod(lambda host, port: True))

    status = NetworkState.check(force=True)

    assert status["state"] == "ONLINE"
    assert status["active_provider"] == "local_slm"
    assert status["details"]["local_model_available"] is True


def test_network_state_reports_desktop_degraded_with_remote_only(monkeypatch):
    NetworkState._last_checked = None
    NetworkState._last_result = {}
    monkeypatch.setenv("IS_DESKTOP_APP", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(NetworkState, "_tcp_reachable", staticmethod(lambda host, port: False))

    status = NetworkState.check(force=True)

    assert status["state"] == "DEGRADED"
    assert status["active_provider"] == "openai"


def test_desktop_runtime_flags_persist(tmp_path, monkeypatch):
    settings_path = tmp_path / "settings.json"
    monkeypatch.setenv("DATALOGIC_STORAGE_SETTINGS_PATH", str(settings_path))

    assert get_local_slm_audit_mode() is True
    assert get_offline_queue_enabled() is True

    assert set_local_slm_audit_mode(False) is False
    assert set_offline_queue_enabled(False) is False
    assert get_local_slm_audit_mode() is False
    assert get_offline_queue_enabled() is False


def test_desktop_offline_queue_lifecycle(tmp_path, monkeypatch):
    queue_path = tmp_path / "offline_queue.json"
    monkeypatch.setenv("DATALOGIC_OFFLINE_QUEUE_PATH", str(queue_path))

    item = enqueue_chat_request({"messages": [{"role": "user", "content": "hello"}]}, reason="test")
    queue = list_queue()

    assert queue["counts"]["pending"] == 1
    assert queue["items"][0]["id"] == item["id"]

    mark_item(item["id"], "completed", response={"run_id": "run-1"})
    queue = list_queue()

    assert queue["counts"]["completed"] == 1
    assert queue["items"][0]["response"]["run_id"] == "run-1"
