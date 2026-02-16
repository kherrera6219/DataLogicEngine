from pathlib import Path

def get_safe_path(base_dir: str, user_path: str) -> str:
    """
    Sanitizes and joins a user-provided path with a base directory.
    Prevents path traversal and ensuring the result is within the base directory.
    """
    base = Path(base_dir).resolve()
    
    # Remove leading separators to prevent absolute path injection
    cleaned_user_path = user_path.lstrip('/\\')
    
    # Join and resolve
    requested_path = (base / cleaned_user_path).resolve()
    
    # Security check: must be a child of base
    if not str(requested_path).startswith(str(base)):
        raise ValueError(f"Security Violation: Path {user_path} is outside of {base_dir}")
        
    return str(requested_path)
