import hashlib
import json
import zipfile
from pathlib import Path

from backend.observability import support_bundle as bundle


SECRET = "sk-1234567890abcdefghijklmnop"
EMAIL = "owner@example.com"
SSN = "123-45-6789"
CONTENT = "private customer prompt sentence"


def _seed_sensitive_files(root: Path) -> None:
    logs = root / "logs"
    reports = root / "reports"
    logs.mkdir(parents=True)
    reports.mkdir(parents=True)
    (logs / "app.log").write_text(
        json.dumps(
            {
                "event": "provider.failure",
                "api_key": SECRET,
                "email": EMAIL,
                "ssn": SSN,
                "prompt": CONTENT,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (logs / "ignored.bin").write_bytes(SECRET.encode("ascii"))
    (reports / "must-not-be-collected.json").write_text(SECRET, encoding="utf-8")


def test_support_redactor_removes_secret_pii_content_and_user_home():
    raw = (
        f"authorization=Bearer {SECRET} email={EMAIL} ssn={SSN} "
        f'"prompt": "{CONTENT}" C:\\Users\\kevin\\private.txt'
    )

    redacted = bundle.redact_support_text(raw)

    assert SECRET not in redacted
    assert EMAIL not in redacted
    assert SSN not in redacted
    assert CONTENT not in redacted
    assert "kevin" not in redacted
    assert "[REDACTED_USER_CONTENT]" in redacted


def test_service_url_removes_credentials_and_query_values():
    sanitized = bundle.redact_service_url(
        "redis://operator:super-secret@127.0.0.1:6379/0?token=hidden"
    )

    assert sanitized == "redis://127.0.0.1:6379/0"


def test_preview_creates_no_archive_and_exposes_only_redacted_inventory(tmp_path):
    _seed_sensitive_files(tmp_path)
    preview = bundle.SupportBundleBuilder(tmp_path).preview(
        options=bundle.SupportBundleOptions(
            include_http=False,
            include_runtime_precheck=False,
        )
    )
    output = json.dumps(preview)

    assert SECRET not in output
    assert "logs/app.log" in output
    assert "reports/" not in output
    assert preview["archive_created"] is False


def test_archive_is_redacted_allowlisted_and_hashed(tmp_path, monkeypatch):
    _seed_sensitive_files(tmp_path)
    output_dir = tmp_path / "output"
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:password@localhost:5432/dle?sslkey=secret")
    monkeypatch.setenv("RATELIMIT_STORAGE_URI", "redis://user:password@localhost:6379/0")
    monkeypatch.setenv("OPENAI_API_KEY", SECRET)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    result = bundle.SupportBundleBuilder(tmp_path).export(
        output_dir,
        options=bundle.SupportBundleOptions(
            include_http=False,
            include_runtime_precheck=False,
        ),
    )
    archive_path = Path(result["archive_path"])
    sidecar_path = Path(result["sidecar_path"])

    assert archive_path.exists()
    assert sidecar_path.exists()
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    assert sidecar_path.read_text(encoding="ascii") == f"{digest}  {archive_path.name}\n"

    with zipfile.ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        assert "logs/app.log" in names
        assert "files.json" in names
        assert not any(name.startswith("reports/") for name in names)
        assert not any(name.endswith("ignored.bin") for name in names)
        combined = b"\n".join(archive.read(name) for name in names)
        assert SECRET.encode("ascii") not in combined
        assert EMAIL.encode("ascii") not in combined
        assert SSN.encode("ascii") not in combined
        assert CONTENT.encode("ascii") not in combined

        environment = json.loads(archive.read("environment_sanitized.json"))
        assert environment["DATABASE_URL"] == "postgresql://localhost:5432/dle"
        assert environment["RATELIMIT_STORAGE_URI"] == "redis://localhost:6379/0"
        assert environment["provider_keys_configured"] == {"openai": True, "google": False}

        inventory = json.loads(archive.read("files.json"))
        for item in inventory:
            data = archive.read(item["path"])
            assert hashlib.sha256(data).hexdigest() == item["sha256"]


def test_optional_encryption_removes_plaintext_archive(tmp_path):
    archive_path = tmp_path / "support.zip"
    archive_path.write_bytes(b"sensitive diagnostics")

    encrypted_path = bundle.encrypt_archive(archive_path, "correct horse battery staple")

    assert not archive_path.exists()
    assert encrypted_path.suffix == ".enc"
    payload = encrypted_path.read_bytes()
    assert payload.startswith(b"DLE-SUPPORT-BUNDLE-ENC-V1\n")
    assert b"sensitive diagnostics" not in payload


def test_support_directory_retention_removes_only_old_owned_archives(tmp_path):
    unrelated = tmp_path / "customer-export.zip"
    unrelated.write_bytes(b"keep")
    archives = []
    for index in range(7):
        path = tmp_path / f"support_bundle_20260714_12000{index}_000000Z.zip"
        path.write_bytes(b"bundle")
        path.with_name(f"{path.name}.sha256").write_text("hash", encoding="ascii")
        path.touch()
        archives.append(path)

    bundle.purge_support_directory(tmp_path, max_archives=5)

    assert unrelated.is_file()
    assert sum(path.is_file() for path in archives) == 5
    for path in archives:
        if not path.exists():
            assert not path.with_name(f"{path.name}.sha256").exists()
