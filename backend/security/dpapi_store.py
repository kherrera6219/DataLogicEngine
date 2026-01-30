import logging
import base64
import os

try:
    import win32crypt
except ImportError:
    win32crypt = None

logger = logging.getLogger("UKG-DPAPI")

# Optional secondary entropy to prevent other apps from decrypting this app's data easily
# In production, this can be set via UKG_DPAPI_ENTROPY env var
_DEFAULT_ENTROPY = "DataLogicEngine_Secret_V1_Pepper"
ENTROPY = os.environ.get("UKG_DPAPI_ENTROPY", _DEFAULT_ENTROPY).encode('utf-8')

def is_available() -> bool:
    """Returns True if DPAPI (win32crypt) is available."""
    return win32crypt is not None

def encrypt_data(data: str) -> str:
    """
    Encrypts data using Windows DPAPI (tied to current user/machine).
    Includes secondary entropy for additional isolation.
    Returns base64 encoded string.
    """
    if not data:
        return ""
    if not is_available():
        logger.error("DPAPI not available on this platform")
        return ""
    try:
        data_bytes = data.encode('utf-8')
        # CryptProtectData(data, description, entropy, reserved, prompt, flags)
        encrypted_bytes = win32crypt.CryptProtectData(data_bytes, "UKG_Data", ENTROPY, None, None, 0)
        return base64.b64encode(encrypted_bytes).decode('utf-8')
    except Exception as e:
        logger.error(f"DPAPI Encryption Failure: {type(e).__name__}")
        return ""

def decrypt_data(encrypted_data_b64: str) -> str:
    """
    Decrypts data using Windows DPAPI.
    Input is base64 encoded string.
    """
    if not encrypted_data_b64:
        return ""
    if not is_available():
        logger.error("DPAPI not available on this platform")
        return ""
    try:
        encrypted_bytes = base64.b64decode(encrypted_data_b64.encode('utf-8'))
        # CryptUnprotectData(data, entropy, reserved, prompt, flags)
        description, decrypted_bytes = win32crypt.CryptUnprotectData(encrypted_bytes, ENTROPY, None, None, 0)
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        logger.error(f"DPAPI Decryption Failure: {type(e).__name__}")
        return ""
