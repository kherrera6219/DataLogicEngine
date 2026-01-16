import win32api
import win32security
import os

def get_windows_user_identity():
    """
    Retrieves the current Windows user's name and SID (Security Identifier).
    Returns a dictionary with 'username' and 'sid'.
    """
    try:
        username = win32api.GetUserName()
        sid, domain, type = win32security.LookupAccountName(None, username)
        sid_string = win32security.ConvertSidToStringSid(sid)
        return {
            "username": username,
            "sid": sid_string,
            "domain": domain
        }
    except Exception as e:
        # Fallback to os.environ if win32 calls fail
        return {
            "username": os.environ.get('USERNAME', 'local_user'),
            "sid": "S-1-5-local-fallback",
            "domain": os.environ.get('USERDOMAIN', 'LOCAL')
        }

if __name__ == "__main__":
    identity = get_windows_user_identity()
    print(f"Windows Identity: {identity}")
