import json

import pytest

from scripts import prepare_semantic_index as cli
from tests.storage.test_semantic_index_preparation import MemoryCollection, _sources


def _args(tmp_path):
    digest = "a" * 64
    return [
        "--port",
        "9000",
        "--source",
        "old",
        "--target",
        "new",
        "--model-path",
        str(tmp_path),
        "--weights-sha256",
        "b" * 64,
        "--manifest-sha256",
        digest,
        "--revision",
        f"semantic-{digest}",
    ]


def test_cli_prepares_only_an_explicit_distinct_target(monkeypatch, tmp_path, capsys):
    source = MemoryCollection("old", _sources())
    target = MemoryCollection("new", revision=f"semantic-{'a' * 64}")
    contacted = []

    class FakeEmbedding:
        def __init__(self, path, **kwargs):
            assert kwargs["expected_manifest_sha256"] == "a" * 64

        def __call__(self, text):
            return [0.6, 0.8]

    class FakeClient:
        def __init__(self, *, host, port):
            contacted.append((host, port))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    monkeypatch.setattr(cli, "LocalSentenceEmbedding", FakeEmbedding)
    monkeypatch.setattr(cli, "ChromaHttpClient", FakeClient)
    monkeypatch.setattr(
        cli,
        "safe_get_collection",
        lambda client, *, name: {"old": source, "new": target}[name],
    )
    cli.main(_args(tmp_path))
    receipt = json.loads(capsys.readouterr().out)
    assert receipt["status"] == "prepared_not_activated"
    assert receipt["record_count"] == 2
    assert contacted == [("127.0.0.1", 9000)]
    assert source.records == target.records


def test_cli_rejects_same_collection_before_contacting_service(monkeypatch, tmp_path):
    def forbidden(*args, **kwargs):
        pytest.fail("must reject before loading the model or contacting storage")

    monkeypatch.setattr(cli, "LocalSentenceEmbedding", forbidden)
    args = _args(tmp_path)
    args[args.index("--target") + 1] = "old"
    with pytest.raises(SystemExit):
        cli.main(args)
