from pathlib import Path

import pytest

from backend.ingestion.acquisition import (
    AcquisitionLimitError,
    SecureAcquisitionSession,
)


def _session(tmp_path, source, **overrides):
    options = {
        "ingestion_id": "ingestion-test",
        "source": source,
        "staging_root": tmp_path / "runtime-staging",
        "supported_extensions": {".txt", ".pdf", ".docx"},
        "max_file_bytes": 1024,
        "max_total_bytes": 4096,
        "max_files": 10,
        "recursive": True,
    }
    options.update(overrides)
    return SecureAcquisitionSession(**options)


def test_acquisition_copies_input_to_bounded_staging_and_cleans_it(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    original = source / "policy.txt"
    original.write_text("policy evidence", encoding="utf-8")

    session = _session(tmp_path, source)
    acquired = session.acquire()

    assert len(acquired.files) == 1
    staged = acquired.files[0]
    assert staged.source_path == original.resolve()
    assert staged.staged_path != staged.source_path
    assert staged.staged_path.read_text(encoding="utf-8") == "policy evidence"
    assert staged.sha256
    assert staged.detected_type == "text"
    assert staged.staged_path.is_relative_to(session.session_root)

    session.cleanup()
    assert not session.session_root.exists()


@pytest.mark.parametrize(
    ("name", "body", "reason"),
    [
        ("spoofed.pdf", b"not a pdf", "content_type_mismatch"),
        ("binary.txt", b"text\x00binary", "binary_text_content"),
    ],
)
def test_acquisition_rejects_extension_content_mismatch(tmp_path, name, body, reason):
    source = tmp_path / "source"
    source.mkdir()
    (source / name).write_bytes(body)

    session = _session(tmp_path, source)
    acquired = session.acquire()

    assert acquired.files == []
    assert len(acquired.rejected) == 1
    assert acquired.rejected[0].reason == reason
    session.cleanup()


def test_acquisition_rejects_links_and_reparse_points(tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    linked = source / "linked.txt"
    linked.write_text("must not follow", encoding="utf-8")

    session = _session(tmp_path, source)
    monkeypatch.setattr(
        session,
        "_is_link_or_reparse",
        lambda path: Path(path).name == "linked.txt",
    )
    acquired = session.acquire()

    assert acquired.files == []
    assert acquired.rejected[0].reason == "link_or_reparse_not_allowed"
    session.cleanup()


def test_acquisition_does_not_resolve_selected_source_before_link_check(
    tmp_path, monkeypatch
):
    source = tmp_path / "selected-link"
    source.mkdir()
    session = _session(tmp_path, source)
    selected = source.absolute()

    monkeypatch.setattr(
        session,
        "_is_link_or_reparse",
        lambda path: Path(path) == selected,
    )

    assert session.source == selected
    with pytest.raises(ValueError, match="ingestion_source_link_or_reparse_not_allowed"):
        session.acquire()


def test_acquisition_enforces_total_job_bytes(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "a.txt").write_bytes(b"a" * 20)
    (source / "b.txt").write_bytes(b"b" * 20)

    session = _session(tmp_path, source, max_total_bytes=30)

    with pytest.raises(AcquisitionLimitError, match="ingestion_total_bytes_exceeded"):
        session.acquire()
    assert not session.session_root.exists()


def test_acquisition_enforces_file_count(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "a.txt").write_text("a", encoding="utf-8")
    (source / "b.txt").write_text("b", encoding="utf-8")

    session = _session(tmp_path, source, max_files=1)

    with pytest.raises(AcquisitionLimitError, match="ingestion_file_count_exceeded"):
        session.acquire()
    assert not session.session_root.exists()


def test_reserved_windows_device_names_are_rejected():
    with pytest.raises(ValueError, match="unsafe_ingestion_filename"):
        SecureAcquisitionSession.validate_relative_path(Path("CON.txt"))


def test_network_and_device_paths_are_rejected_before_access(tmp_path):
    with pytest.raises(ValueError, match="network_ingestion_source_not_allowed"):
        SecureAcquisitionSession(
            ingestion_id="ingestion-network",
            source=r"\\server\share\corpus",
            staging_root=tmp_path / "staging",
            supported_extensions={".txt"},
            max_file_bytes=1024,
            max_total_bytes=4096,
            max_files=10,
            recursive=True,
        )
