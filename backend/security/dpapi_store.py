import win32crypt
import base64

# Optional secondary entropy to prevent other apps from decrypting this app's data easily
# In production, this could be a machine-unique value or a hardcoded pepper
ENTROPY = "DataLogicEngine_Secret_V1_Pepper".encode('utf-8')

def encrypt_data(data: str) -> str:
    """
    Encrypts data using Windows DPAPI (tied to current user/machine).
    Includes secondary entropy for additional isolation.
    Returns base64 encoded string.
    """
    if not data:
        return ""
    try:
        data_bytes = data.encode('utf-8')
        # CryptProtectData(data, description, entropy, reserved, prompt, flags)
        encrypted_bytes = win32crypt.CryptProtectData(data_bytes, "UKG_Data", ENTROPY, None, None, 0)
        return base64.b64encode(encrypted_bytes).decode('utf-8')
    except Exception as e:
        # Avoid logging the sensitive data itself
        print(f"DPAPI Encryption Root Failure: {type(e).__name__}")
        return ""

def decrypt_data(encrypted_data_b64: str) -> str:
    """
    Decrypts data using Windows DPAPI.
    Input is base64 encoded string.
    """
    if not encrypted_data_b64:
        return ""
    try:
        encrypted_bytes = base64.b64decode(encrypted_data_b64.encode('utf-8'))
        # CryptUnprotectData(data, entropy, reserved, prompt, flags)
        description, decrypted_bytes = win32crypt.CryptUnprotectData(encrypted_bytes, ENTROPY, None, None, 0)
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        print(f"DPAPI Decryption Root Failure: {type(e).__name__}")
        return ""

if __name__ == "__main__":
    secret = "sk-openai-123456789"
    encrypted = encrypt_data(secret)
    print(f"Encrypted: {encrypted}")
    decrypted = decrypt_data(encrypted)
    print(f"Decrypted: {decrypted}")
    assert secret == decrypted, "Decryption failed to match original secret"
