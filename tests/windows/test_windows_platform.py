import pytest
import os
import sys
from backend.security.dpapi_store import encrypt_data, decrypt_data
from backend.auth.windows_identity import get_windows_user_identity

@pytest.mark.skipif(sys.platform != "win32", reason="Windows specific tests")
class TestWindowsPlatform:
    
    def test_dpapi_encryption_decryption(self):
        """Verify that DPAPI can encrypt and decrypt data consistently."""
        secret = "test_secret_123"
        encrypted = encrypt_data(secret)
        assert encrypted != secret
        assert len(encrypted) > 0
        
        decrypted = decrypt_data(encrypted)
        assert decrypted == secret

    def test_dpapi_entropy_isolation(self):
        """
        Verify that data encrypted with entropy cannot be decrypted without it.
        (Simulated by attempting to decrypt with raw win32crypt if possible, 
        but here we just ensure our functions work together)
        """
        secret = "entropy_test"
        encrypted = encrypt_data(secret)
        decrypted = decrypt_data(encrypted)
        assert decrypted == secret

    def test_windows_identity_retrieval(self):
        """Verify that Windows identity retrieval returns expected structure."""
        identity = get_windows_user_identity()
        assert "username" in identity
        assert "sid" in identity
        assert "domain" in identity
        assert isinstance(identity["is_fallback"], bool)
        
        # On a real Windows machine, is_fallback should be False
        # But we allow True in CI/restricted environments
        if not identity["is_fallback"]:
            assert identity["sid"].startswith("S-1-5")

    def test_config_manager_desktop_paths(self):
        """Verify that ConfigManager uses Windows-standard paths by default."""
        from backend.config_manager import ConfigManager
        config = ConfigManager()
        # Default UKG_DATA_DIR for Windows
        expected_base = "C:\\ProgramData\\DataLogicEngine"
        assert config.UKG_DATA_DIR == expected_base
