import io
from pathlib import Path
import zipfile

from pypdf import PdfWriter

from backend.ingestion.local_ingestion import (
    LocalKnowledgeIngestionService,
    _bounded_binary_document_worker,
)


class Output:
    def __init__(self):
        self.value = None

    def put(self, value):
        self.value = value


def _run_worker(path, mime, **overrides):
    output = Output()
    options = {
        "max_pages": 10,
        "max_archive_entries": 10,
        "max_decompressed_bytes": 1024,
        "max_archive_depth": 1,
    }
    options.update(overrides)
    _bounded_binary_document_worker(
        str(path),
        mime,
        options["max_pages"],
        options["max_archive_entries"],
        options["max_decompressed_bytes"],
        options["max_archive_depth"],
        output,
    )
    return output.value


def test_pdf_page_limit_is_checked_before_text_extraction(tmp_path):
    path = tmp_path / "pages.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.add_blank_page(width=100, height=100)
    with path.open("wb") as handle:
        writer.write(handle)

    assert _run_worker(path, "application/pdf", max_pages=1) == (
        "error",
        "document_page_limit_exceeded",
    )


def test_encrypted_pdf_is_rejected_before_text_extraction(tmp_path):
    path = tmp_path / "encrypted.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("owner-secret")
    with path.open("wb") as handle:
        writer.write(handle)

    assert _run_worker(path, "application/pdf") == (
        "error",
        "encrypted_document_not_allowed",
    )


def test_docx_archive_path_and_expansion_limits_fail_closed(tmp_path):
    traversal = tmp_path / "traversal.docx"
    with zipfile.ZipFile(traversal, "w") as archive:
        archive.writestr("../escape.xml", "unsafe")
    assert _run_worker(
        traversal,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ) == ("error", "archive_path_traversal")

    expansion = tmp_path / "expansion.docx"
    with zipfile.ZipFile(expansion, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", "x" * 200)
    assert _run_worker(
        expansion,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        max_decompressed_bytes=100,
    ) == ("error", "archive_decompression_limit_exceeded")


def test_nested_docx_archive_respects_depth_limit(tmp_path):
    path = tmp_path / "nested.docx"
    nested = io.BytesIO()
    with zipfile.ZipFile(nested, "w") as archive:
        archive.writestr("nested.txt", "content")
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("word/embeddings/payload.zip", nested.getvalue())

    assert _run_worker(
        path,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ) == ("error", "archive_depth_exceeded")


def test_parser_timeout_terminates_child_process(tmp_path, monkeypatch):
    class FakeQueue:
        def close(self):
            return None

    class FakeProcess:
        def __init__(self):
            self.terminated = False

        def start(self):
            return None

        def join(self, timeout=None):
            return None

        def is_alive(self):
            return not self.terminated

        def terminate(self):
            self.terminated = True

    process = FakeProcess()

    class FakeContext:
        def Queue(self, maxsize=1):
            return FakeQueue()

        def Process(self, **kwargs):
            return process

    monkeypatch.setattr(
        "backend.ingestion.local_ingestion.multiprocessing.get_context",
        lambda _method: FakeContext(),
    )
    path = tmp_path / "slow.pdf"
    path.write_bytes(b"%PDF-1.7")
    service = LocalKnowledgeIngestionService(
        staging_root=tmp_path / "staging", parser_timeout_seconds=1
    )

    assert service._extract_via_document_processor(Path(path), ".pdf") == (
        "",
        "document_parser_timeout",
    )
    assert process.terminated is True
