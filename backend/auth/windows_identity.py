import win32api
import win32security
import os

def get_windows_user_identity():
    """
    Retrieves the current Windows user's name and SID (Security Identifier).
    Returns a dictionary with 'username', 'sid', and 'domain'.
    """
    try:
        username = win32api.GetUserName()
        sid, domain, type = win32security.LookupAccountName(None, username)
        sid_string = win32security.ConvertSidToStringSid(sid)
        
        # Validation: Ensure SID is a non-empty string starting with 'S-'
        if not sid_string or not sid_string.startswith("S-") or len(sid_string) < 12:
            raise ValueError(f"Invalid SID format retrieved: {sid_string}")

        return {
            "username": username,
            "sid": sid_string,
            "domain": domain,
            "is_fallback": False
        }
    except Exception as e:
        # Log failure type but don't crash
        print(f"Windows Identity Retrieval Failed: {type(e).__name__}")
        # Fallback to environment variables if win32 calls fail
        # This is strictly for local-first execution in restricted environments
        return {
            "username": os.environ.get('USERNAME', 'local_user'),
            "sid": "S-1-5-local-fallback",
            "domain": os.environ.get('USERDOMAIN', 'LOCAL'),
            "is_fallback": True
        }

if __name__ == "__main__":
    identity = get_windows_user_identity()
    print(f"Windows Identity: {identity}")
