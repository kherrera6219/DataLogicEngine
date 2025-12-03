"""
HTML Sanitizer

Provides HTML sanitization to prevent XSS attacks.
Uses bleach library for safe HTML cleaning.
"""

import bleach
import logging
from typing import List, Optional, Set

logger = logging.getLogger(__name__)


class HTMLSanitizer:
    """
    HTML sanitization for user-generated content.

    Removes dangerous tags and attributes that could be used for XSS attacks.
    """

    # Safe tags allowed in user content
    ALLOWED_TAGS: Set[str] = {
        # Text formatting
        'p', 'br', 'span', 'div',
        'strong', 'b', 'em', 'i', 'u', 's',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        # Lists
        'ul', 'ol', 'li',
        # Links
        'a',
        # Code
        'pre', 'code',
        # Tables
        'table', 'thead', 'tbody', 'tr', 'th', 'td',
        # Quotes
        'blockquote', 'q',
    }

    # Safe attributes allowed for specific tags
    ALLOWED_ATTRIBUTES: dict = {
        'a': ['href', 'title', 'rel'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'code': ['class'],  # For syntax highlighting
        'pre': ['class'],
        '*': ['class', 'id'],  # Allow class and id on all tags
    }

    # Safe URL protocols
    ALLOWED_PROTOCOLS: List[str] = ['http', 'https', 'mailto']

    @classmethod
    def sanitize(cls, html: str, strip: bool = False) -> str:
        """
        Sanitize HTML content.

        Args:
            html: HTML string to sanitize
            strip: If True, strip tags instead of escaping them

        Returns:
            Sanitized HTML string
        """
        if not html:
            return ''

        try:
            cleaned = bleach.clean(
                html,
                tags=cls.ALLOWED_TAGS if not strip else [],
                attributes=cls.ALLOWED_ATTRIBUTES,
                protocols=cls.ALLOWED_PROTOCOLS,
                strip=strip,
                strip_comments=True
            )

            logger.debug("HTML sanitized successfully")
            return cleaned

        except Exception as e:
            logger.error(f"Error sanitizing HTML: {str(e)}")
            # On error, strip all tags as a safety measure
            return bleach.clean(html, tags=[], strip=True)

    @classmethod
    def sanitize_strict(cls, html: str) -> str:
        """
        Strictly sanitize HTML - strip all tags.

        Args:
            html: HTML string to sanitize

        Returns:
            Plain text with all HTML removed
        """
        return cls.sanitize(html, strip=True)

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Sanitize plain text input.

        Escapes HTML entities but preserves line breaks.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text with HTML entities escaped
        """
        if not text:
            return ''

        try:
            # Use bleach's linkify to make URLs clickable (optional)
            # For now, just escape HTML entities
            return bleach.clean(text, tags=[], strip=True)

        except Exception as e:
            logger.error(f"Error sanitizing text: {str(e)}")
            return ''

    @classmethod
    def linkify(cls, text: str, skip_tags: Optional[List[str]] = None) -> str:
        """
        Convert URLs in text to clickable links.

        Args:
            text: Text containing URLs
            skip_tags: Tags to skip linkifying (e.g., ['pre', 'code'])

        Returns:
            Text with URLs converted to links
        """
        if not text:
            return ''

        try:
            skip_tags = skip_tags or ['pre', 'code']

            linked = bleach.linkify(
                text,
                skip_tags=skip_tags,
                parse_email=False  # Don't linkify emails for privacy
            )

            logger.debug("Text linkified successfully")
            return linked

        except Exception as e:
            logger.error(f"Error linkifying text: {str(e)}")
            return text


# Convenience functions
def sanitize_html(html: str, strict: bool = False) -> str:
    """
    Sanitize HTML content.

    Args:
        html: HTML to sanitize
        strict: If True, strip all HTML tags

    Returns:
        Sanitized HTML
    """
    if strict:
        return HTMLSanitizer.sanitize_strict(html)
    return HTMLSanitizer.sanitize(html)


def sanitize_text(text: str) -> str:
    """
    Sanitize plain text content.

    Args:
        text: Text to sanitize

    Returns:
        Sanitized text
    """
    return HTMLSanitizer.sanitize_text(text)


def linkify_text(text: str) -> str:
    """
    Convert URLs in text to links.

    Args:
        text: Text with URLs

    Returns:
        Text with clickable links
    """
    return HTMLSanitizer.linkify(text)


# Flask integration
def sanitize_form_data(form_data: dict, fields: List[str]) -> dict:
    """
    Sanitize specific fields in form data.

    Args:
        form_data: Dictionary of form data
        fields: List of fields to sanitize

    Returns:
        Form data with sanitized fields
    """
    sanitized = form_data.copy()

    for field in fields:
        if field in sanitized:
            value = sanitized[field]
            if isinstance(value, str):
                sanitized[field] = sanitize_text(value)
            elif isinstance(value, list):
                sanitized[field] = [sanitize_text(v) if isinstance(v, str) else v for v in value]

    return sanitized


def sanitize_json_data(json_data: dict, fields: List[str]) -> dict:
    """
    Sanitize specific fields in JSON data.

    Args:
        json_data: Dictionary of JSON data
        fields: List of fields to sanitize

    Returns:
        JSON data with sanitized fields
    """
    return sanitize_form_data(json_data, fields)
