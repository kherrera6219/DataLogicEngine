import pytest
from unittest.mock import MagicMock, patch

from backend.storage.graph_store import GraphStore
from backend.storage.object_store import LocalFileBackend


def test_graph_store_rejects_invalid_node_label():
    store = GraphStore()
    store.run_query = MagicMock(return_value=[{"n": {"id": "1"}}])

    result = store.create_node("User) DETACH DELETE n //", {"id": "1"})

    assert result is False
    store.run_query.assert_not_called()


def test_graph_store_rejects_invalid_relationship_type():
    store = GraphStore()
    store.run_query = MagicMock(return_value=[{"r": {"id": "1"}}])

    result = store.create_relationship("a", "b", "REL-TYPE")

    assert result is False
    store.run_query.assert_not_called()


def test_graph_store_blocks_default_password_in_production(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    store = GraphStore()

    with patch("backend.storage.graph_store.GraphDatabase.driver") as mock_driver:
        store.connect()
        mock_driver.assert_not_called()
        assert store.driver is None


def test_local_object_store_rejects_path_traversal(tmp_path):
    backend = LocalFileBackend(base_path=str(tmp_path))

    with pytest.raises(ValueError):
        backend.put("docs", "../escape.txt", b"payload")

    assert backend.exists("docs", "../escape.txt") is False


def test_local_object_store_rejects_invalid_bucket_name(tmp_path):
    backend = LocalFileBackend(base_path=str(tmp_path))

    with pytest.raises(ValueError):
        backend.put("../bad", "a.txt", b"payload")

    assert backend.create_bucket("../bad") is False


def test_local_object_store_normalizes_windows_separators(tmp_path):
    backend = LocalFileBackend(base_path=str(tmp_path))
    backend.put("docs", "nested\\folder\\a.txt", b"hello")

    assert backend.exists("docs", "nested/folder/a.txt")
    assert backend.get("docs", "nested/folder/a.txt") == b"hello"
