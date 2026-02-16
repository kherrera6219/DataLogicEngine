import unittest
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

@unittest.skipUnless(sys.platform == "win32", "DPAPI tests require Windows")
class TestDPAPICrypto(unittest.TestCase):
    def test_encryption_decryption_flow(self):
        """Verify that data can be encrypted and decrypted correctly."""
        from backend.security.dpapi_store import encrypt_data, decrypt_data
        
        test_secret = "ukg_test_secret_12345"
        
        try:
            # Encrypt
            encrypted = encrypt_data(test_secret)
            self.assertIsNotNone(encrypted)
            self.assertNotEqual(encrypted, test_secret)
            
            # Decrypt
            decrypted = decrypt_data(encrypted)
            self.assertEqual(decrypted, test_secret)
            print("DPAPI Roundtrip: SUCCESS")
        except Exception as e:
            # If win32crypt is not available/working, this might fail on non-Windows
            # but we assume we are on Windows as per metadata.
            self.fail(f"DPAPI operation failed: {e}")

    def test_decryption_failure_safe(self):
        """Verify that invalid data doesn't crash the decryptor."""
        from backend.security.dpapi_store import decrypt_data
        
        result = decrypt_data("not-base64-and-not-encrypted")
        self.assertEqual(result, "")

if __name__ == "__main__":
    unittest.main()
