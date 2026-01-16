import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

def test_windows_identity():
    print("Testing Windows Identity Resolution...")
    try:
        from backend.auth.windows_identity import get_windows_user_identity
        identity = get_windows_user_identity()
        print(f"Success: {identity}")
        assert 'sid' in identity
        assert 'username' in identity
    except Exception as e:
        print(f"Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def test_dpapi_encryption():
    print("Testing DPAPI Encryption/Decryption...")
    try:
        from backend.security.dpapi_store import encrypt_data, decrypt_data

        original = "test-secret-123"
        encrypted = encrypt_data(original)
        decrypted = decrypt_data(encrypted)
        print(f"Original: {original}")
        print(f"Encrypted: {encrypted}")
        print(f"Decrypted: {decrypted}")
        assert original == decrypted
        print("Success: Encryption/Decryption verified")
    except Exception as e:
        print(f"Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if os.name != 'nt':
        print("Skipping Windows tests on non-Windows platform")
        sys.exit(0)
        
    test_windows_identity()
    print("-" * 20)
    test_dpapi_encryption()
    print("-" * 20)
    print("All Windows component tests passed!")
