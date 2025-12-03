"""
HTML Sanitization Module

Provides comprehensive HTML sanitization to prevent XSS attacks.
Uses Bleach library to clean user-generated HTML content.

Features:
- Whitelist-based HTML sanitization
- Configurable allowed tags and attributes
- URL protocol validation
- CSS property filtering
- Automatic link rel="nofollow" for user content
"""

import re
from typing import Optional, List, Dict, Set
import logging

try:
    import bleach
    from bleach.css_sanitizer import CSSSanitizer
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False
    logging.warning("Bleach not installed. HTML sanitization will use basic regex fallback.")

logger = logging.getLogger(__name__)


# ========================================
# Sanitization Profiles
# ========================================

# Strict profile: Only basic formatting, no links
STRICT_ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'b', 'i',
    'ul', 'ol', 'li',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'code', 'pre'
]

STRICT_ALLOWED_ATTRIBUTES = {
    '*': ['class'],  # Allow class on all elements for styling
}

# Standard profile: Basic formatting + links
STANDARD_ALLOWED_TAGS = STRICT_ALLOWED_TAGS + [
    'a', 'abbr', 'acronym', 'cite', 'span', 'div'
]

STANDARD_ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id'],
    'a': ['href', 'title', 'rel'],
    'abbr': ['title'],
    'acronym': ['title'],
}

# Rich profile: Extended formatting (for trusted users)
RICH_ALLOWED_TAGS = STANDARD_ALLOWED_TAGS + [
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'img', 'hr', 'dl', 'dt', 'dd',
    'sup', 'sub', 'del', 'ins'
]

RICH_ALLOWED_ATTRIBUTES = {
    '*': ['class', 'id', 'style'],
    'a': ['href', 'title', 'rel', 'target'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'table': ['border', 'cellpadding', 'cellspacing'],
    'td': ['colspan', 'rowspan'],
    'th': ['colspan', 'rowspan'],
}

# Allowed URL protocols
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto', 'ftp']

# Allowed CSS properties (for rich profile)
ALLOWED_CSS_PROPERTIES = [
    'color', 'background-color', 'font-size', 'font-weight', 'font-style',
    'text-align', 'text-decoration', 'margin', 'padding',
    'border', 'border-radius', 'width', 'height'
]


class HTMLSanitizer:
    """
    HTML sanitization utility for preventing XSS attacks.

    Provides multiple sanitization profiles:
    - strict: Minimal HTML (no links)
    - standard: Basic formatting + links (default)
    - rich: Extended formatting (for trusted users)
    - none: Strip all HTML
    """

    def __init__(self, profile: str = 'standard'):
        """
        Initialize HTML sanitizer with specified profile.

        Args:
            profile: Sanitization profile ('strict', 'standard', 'rich', 'none')
        """
        self.profile = profile
        self.bleach_available = BLEACH_AVAILABLE

        if not self.bleach_available:
            logger.warning(f"HTMLSanitizer initialized without Bleach library (profile: {profile})")

    def sanitize(self, html: str, profile: Optional[str] = None) -> str:
        """
        Sanitize HTML content based on profile.

        Args:
            html: HTML content to sanitize
            profile: Optional profile override

        Returns:
            Sanitized HTML string

        Example:
            sanitizer = HTMLSanitizer('standard')
            clean_html = sanitizer.sanitize('<script>alert("XSS")</script><p>Safe content</p>')
            # Returns: '<p>Safe content</p>'
        """
        if not html:
            return ''

        # Use instance profile if not overridden
        active_profile = profile or self.profile

        # Handle 'none' profile - strip all HTML
        if active_profile == 'none':
            return self._strip_all_html(html)

        # Use Bleach if available, otherwise fallback to regex
        if self.bleach_available:
            return self._sanitize_with_bleach(html, active_profile)
        else:
            return self._sanitize_with_regex(html)

    def _sanitize_with_bleach(self, html: str, profile: str) -> str:
        """
        Sanitize HTML using Bleach library (whitelist-based).

        Args:
            html: HTML content
            profile: Sanitization profile

        Returns:
            Sanitized HTML
        """
        # Get profile configuration
        if profile == 'strict':
            allowed_tags = STRICT_ALLOWED_TAGS
            allowed_attributes = STRICT_ALLOWED_ATTRIBUTES
            css_sanitizer = None
        elif profile == 'rich':
            allowed_tags = RICH_ALLOWED_TAGS
            allowed_attributes = RICH_ALLOWED_ATTRIBUTES
            css_sanitizer = CSSSanitizer(allowed_css_properties=ALLOWED_CSS_PROPERTIES)
        else:  # standard (default)
            allowed_tags = STANDARD_ALLOWED_TAGS
            allowed_attributes = STANDARD_ALLOWED_ATTRIBUTES
            css_sanitizer = None

        # Sanitize HTML
        clean_html = bleach.clean(
            html,
            tags=allowed_tags,
            attributes=allowed_attributes,
            protocols=ALLOWED_PROTOCOLS,
            strip=True,  # Strip disallowed tags instead of escaping
            css_sanitizer=css_sanitizer
        )

        # Add rel="nofollow" to user-generated links (anti-spam)
        if profile in ['standard', 'rich']:
            clean_html = bleach.linkify(
                clean_html,
                callbacks=[self._add_nofollow],
                skip_tags=['pre', 'code']
            )

        return clean_html

    def _sanitize_with_regex(self, html: str) -> str:
        """
        Fallback sanitization using regex (less secure, basic only).

        WARNING: This is a basic fallback. Install Bleach for production use!

        Args:
            html: HTML content

        Returns:
            Sanitized HTML
        """
        logger.warning("Using regex-based HTML sanitization (fallback). Install Bleach for better security.")

        # Remove script tags and their content
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # Remove iframe tags
        html = re.sub(r'<iframe[^>]*>.*?</iframe>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # Remove style tags
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # Remove event handlers (onclick, onload, etc.)
        html = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', html, flags=re.IGNORECASE)
        html = re.sub(r'\s*on\w+\s*=\s*\S+', '', html, flags=re.IGNORECASE)

        # Remove javascript: protocol
        html = re.sub(r'javascript:', '', html, flags=re.IGNORECASE)

        # Remove data: protocol (can be used for XSS)
        html = re.sub(r'data:', '', html, flags=re.IGNORECASE)

        return html

    def _strip_all_html(self, html: str) -> str:
        """
        Strip all HTML tags, leaving only text content.

        Args:
            html: HTML content

        Returns:
            Plain text
        """
        if self.bleach_available:
            return bleach.clean(html, tags=[], strip=True)
        else:
            # Basic regex fallback
            return re.sub(r'<[^>]+>', '', html)

    @staticmethod
    def _add_nofollow(attrs, new=False):
        """
        Callback to add rel="nofollow" to links (anti-spam).

        Args:
            attrs: Link attributes
            new: Whether link was created by linkify

        Returns:
            Modified attributes
        """
        # Get or create rel attribute
        rel_values = set(attrs.get((None, 'rel'), '').split())
        rel_values.add('nofollow')
        attrs[(None, 'rel')] = ' '.join(rel_values)

        return attrs


# ========================================
# Convenience Functions
# ========================================

def sanitize_html(html: str, profile: str = 'standard') -> str:
    """
    Convenience function to sanitize HTML content.

    Args:
        html: HTML content to sanitize
        profile: Sanitization profile ('strict', 'standard', 'rich', 'none')

    Returns:
        Sanitized HTML string

    Example:
        from backend.security.html_sanitizer import sanitize_html

        clean = sanitize_html('<p>Safe</p><script>alert("XSS")</script>', 'standard')
        # Returns: '<p>Safe</p>'
    """
    sanitizer = HTMLSanitizer(profile)
    return sanitizer.sanitize(html)


def strip_html(html: str) -> str:
    """
    Strip all HTML tags, leaving only text.

    Args:
        html: HTML content

    Returns:
        Plain text

    Example:
        text = strip_html('<p>Hello <strong>World</strong></p>')
        # Returns: 'Hello World'
    """
    return sanitize_html(html, profile='none')


def sanitize_user_input(text: str, allow_html: bool = False) -> str:
    """
    Sanitize user input for safe display.

    Args:
        text: User input text
        allow_html: Whether to allow HTML (sanitized) or strip it

    Returns:
        Sanitized text

    Example:
        # No HTML allowed (default)
        safe_text = sanitize_user_input('<script>alert("XSS")</script>Hello')
        # Returns: 'alert("XSS")Hello' (HTML stripped)

        # HTML allowed (sanitized)
        safe_html = sanitize_user_input('<p>Hello</p><script>alert("XSS")</script>', allow_html=True)
        # Returns: '<p>Hello</p>' (script removed)
    """
    if not text:
        return ''

    if allow_html:
        return sanitize_html(text, profile='standard')
    else:
        return strip_html(text)


# ========================================
# Flask Integration Helpers
# ========================================

def sanitize_json_fields(data: dict, fields: List[str], profile: str = 'standard') -> dict:
    """
    Sanitize specific fields in a JSON/dict object.

    Args:
        data: Dictionary with data
        fields: List of field names to sanitize
        profile: Sanitization profile

    Returns:
        Dictionary with sanitized fields

    Example:
        data = {
            'username': 'john',
            'bio': '<script>alert("XSS")</script><p>Hello</p>',
            'description': '<p>Safe content</p>'
        }
        sanitized = sanitize_json_fields(data, ['bio', 'description'], 'standard')
        # bio and description fields are sanitized
    """
    sanitizer = HTMLSanitizer(profile)
    sanitized_data = data.copy()

    for field in fields:
        if field in sanitized_data and isinstance(sanitized_data[field], str):
            sanitized_data[field] = sanitizer.sanitize(sanitized_data[field])

    return sanitized_data


def sanitize_request_decorator(fields: List[str], profile: str = 'standard'):
    """
    Decorator to automatically sanitize request JSON fields.

    Args:
        fields: List of field names to sanitize
        profile: Sanitization profile

    Example:
        from flask import request, jsonify
        from backend.security.html_sanitizer import sanitize_request_decorator

        @app.route('/api/posts', methods=['POST'])
        @sanitize_request_decorator(['title', 'content'], 'standard')
        def create_post():
            data = request.get_json()
            # data['title'] and data['content'] are now sanitized
            ...
    """
    from functools import wraps
    from flask import request

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.is_json:
                # Get request data
                data = request.get_json()

                # Sanitize specified fields
                sanitized_data = sanitize_json_fields(data, fields, profile)

                # Replace request data with sanitized version
                # Note: This modifies request.json (hacky but works)
                request.get_json = lambda force=False, silent=False, cache=True: sanitized_data

            return f(*args, **kwargs)

        return decorated_function
    return decorator


# ========================================
# Installation Check
# ========================================

def check_bleach_installation() -> tuple:
    """
    Check if Bleach is properly installed.

    Returns:
        Tuple of (is_installed: bool, message: str)

    Example:
        is_installed, message = check_bleach_installation()
        if not is_installed:
            print(f"WARNING: {message}")
    """
    if BLEACH_AVAILABLE:
        try:
            import bleach
            version = bleach.__version__
            return True, f"Bleach {version} is installed and ready"
        except Exception as e:
            return False, f"Bleach import failed: {str(e)}"
    else:
        return False, "Bleach is not installed. Install with: pip install bleach==6.1.0"


# ========================================
# Module Initialization
# ========================================

if __name__ == '__main__':
    # Test sanitization
    print("HTML Sanitization Test\n" + "=" * 50)

    test_html = """
    <p>This is <strong>safe</strong> content.</p>
    <script>alert('XSS Attack!');</script>
    <a href="javascript:alert('XSS')">Malicious Link</a>
    <a href="https://example.com" onclick="alert('XSS')">Safe Link</a>
    <img src="x" onerror="alert('XSS')">
    """

    print(f"\nOriginal HTML:\n{test_html}")

    profiles = ['strict', 'standard', 'rich', 'none']
    for profile in profiles:
        sanitized = sanitize_html(test_html, profile)
        print(f"\nProfile '{profile}':\n{sanitized}")

    # Check installation
    is_installed, message = check_bleach_installation()
    print(f"\n\nBleach Installation: {message}")
