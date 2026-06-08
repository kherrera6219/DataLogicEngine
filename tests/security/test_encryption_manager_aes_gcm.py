import base64
from pathlib import Path

from cryptography.fernet import Fernet

from backend.security.encryption_manager import (
    AES_256_GCM_ALGORITHM,
    FERNET_ALGORITHM,
    EncryptionManager,
)


def test_encryption_manager_writes_aes_256_gcm_payloads(tmp_path, monkeypatch):
    monkeypatch.setenv("ENCRYPTION_KEK_SECRET", "test-secret-for-aes-gcm")

    manager = EncryptionManager(key_dir=str(tmp_path / "keys"))

    encrypted = manager.encrypt("sensitive-value", field_name="secret")

    assert encrypted.startswith("v1:")
    assert manager.decrypt(encrypted, field_name="secret") == "sensitive-value"
    assert manager.dek_registry["keys"][0]["algorithm"] == AES_256_GCM_ALGORITHM


def test_encryption_manager_decrypts_legacy_fernet_version(tmp_path, monkeypatch):
    monkeypatch.setenv("ENCRYPTION_KEK_SECRET", "test-secret-for-legacy-fernet")

    key_dir = tmp_path / "keys"
    manager = EncryptionManager(key_dir=str(key_dir))

    legacy_dek = Fernet.generate_key()
    manager.dek_registry["keys"][0]["algorithm"] = FERNET_ALGORITHM
    manager.dek_registry["keys"][0]["encrypted_key"] = base64.b64encode(
        manager._kek.encrypt(legacy_dek)
    ).decode("utf-8")
    manager._save_dek_registry()

    legacy_payload = Fernet(legacy_dek).encrypt(b"legacy-value")
    encrypted = f"v1:{base64.b64encode(legacy_payload).decode('utf-8')}"

    reloaded = EncryptionManager(key_dir=str(Path(key_dir)))

    assert reloaded.decrypt(encrypted, field_name="legacy") == "legacy-value"
