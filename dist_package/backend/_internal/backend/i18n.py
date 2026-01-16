"""
Internationalization (i18n) Configuration for DataLogicEngine

Uses Flask-Babel for multi-language support.
"""

import os
from flask import Flask, request, g
from flask_babel import Babel, gettext, lazy_gettext

babel = Babel()

# Supported languages
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'de': 'Deutsch',
    'zh': '中文',
    'ja': '日本語',
    'ko': '한국어',
    'pt': 'Português',
    'ru': 'Русский',
    'ar': 'العربية'
}

DEFAULT_LANGUAGE = 'en'


def get_locale():
    """
    Select the best matching language for the user.
    
    Priority:
    1. User preference (if logged in)
    2. Session language
    3. Accept-Language header
    4. Default language
    """
    # Check if user has set a language preference
    from flask_login import current_user
    
    if hasattr(current_user, 'language') and current_user.is_authenticated:
        if current_user.language in SUPPORTED_LANGUAGES:
            return current_user.language
    
    # Check session
    from flask import session
    if 'language' in session and session['language'] in SUPPORTED_LANGUAGES:
        return session['language']
    
    # Check Accept-Language header
    return request.accept_languages.best_match(SUPPORTED_LANGUAGES.keys(), default=DEFAULT_LANGUAGE)


def get_timezone():
    """Get user's timezone."""
    from flask_login import current_user
    
    if hasattr(current_user, 'timezone') and current_user.is_authenticated:
        return current_user.timezone
    
    return os.environ.get('DEFAULT_TIMEZONE', 'UTC')


def init_babel(app: Flask) -> None:
    """Initialize Babel with Flask app."""
    app.config.setdefault('BABEL_DEFAULT_LOCALE', DEFAULT_LANGUAGE)
    app.config.setdefault('BABEL_DEFAULT_TIMEZONE', 'UTC')
    app.config.setdefault('BABEL_TRANSLATION_DIRECTORIES', 'translations')
    
    babel.init_app(app, locale_selector=get_locale, timezone_selector=get_timezone)
    
    # Add supported languages to app config
    app.config['SUPPORTED_LANGUAGES'] = SUPPORTED_LANGUAGES
    
    @app.context_processor
    def inject_i18n():
        """Inject i18n helpers into templates."""
        return {
            'get_locale': get_locale,
            'supported_languages': SUPPORTED_LANGUAGES
        }


# Convenience aliases
_ = gettext
_l = lazy_gettext


# Common translatable strings
COMMON_STRINGS = {
    'welcome': _l('Welcome'),
    'login': _l('Login'),
    'logout': _l('Logout'),
    'register': _l('Register'),
    'dashboard': _l('Dashboard'),
    'settings': _l('Settings'),
    'profile': _l('Profile'),
    'save': _l('Save'),
    'cancel': _l('Cancel'),
    'delete': _l('Delete'),
    'edit': _l('Edit'),
    'search': _l('Search'),
    'loading': _l('Loading...'),
    'error': _l('Error'),
    'success': _l('Success'),
    'warning': _l('Warning'),
    'info': _l('Information'),
    'confirm': _l('Confirm'),
    'yes': _l('Yes'),
    'no': _l('No'),
}
