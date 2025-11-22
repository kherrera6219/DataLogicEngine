"""
Validation utilities for UKG system
"""


def isValidEmail(email):
    """
    Validates email format

    Args:
        email (str): Email address to validate

    Returns:
        bool: True if valid email format
    """
    if not email or not isinstance(email, str):
        return False

    import re
    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return re.match(email_regex, email) is not None


def validatePassword(password):
    """
    Validates password strength

    Args:
        password (str): Password to validate

    Returns:
        dict: Object with {valid: bool, errors: list}
    """
    errors = []

    if not password or not isinstance(password, str):
        errors.append('Password is required')
        return {'valid': False, 'errors': errors}

    if len(password) < 8:
        errors.append('Password must be at least 8 characters long')

    import re
    if not re.search(r'[A-Z]', password):
        errors.append('Password must contain at least one uppercase letter')

    if not re.search(r'[a-z]', password):
        errors.append('Password must contain at least one lowercase letter')

    if not re.search(r'[0-9]', password):
        errors.append('Password must contain at least one number')

    if not re.search(r'[!@#$%^&*]', password):
        errors.append('Password must contain at least one special character (!@#$%^&*)')

    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def sanitizeInput(input_str):
    """
    Sanitizes user input to prevent XSS

    Args:
        input_str (str): User input to sanitize

    Returns:
        str: Sanitized input
    """
    if not input_str or not isinstance(input_str, str):
        return ''

    return (input_str
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#x27;')
            .replace('/', '&#x2F;'))
