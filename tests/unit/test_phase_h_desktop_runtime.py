import os

from backend.llm_gateway.gateway import NetworkState
from backend.storage.database_manager import DatabaseLifecycleManager


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
