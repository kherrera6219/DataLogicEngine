# HTML Sanitization Guide

**Preventing XSS Attacks in DataLogicEngine**

This guide covers HTML sanitization implementation using the Bleach library to prevent Cross-Site Scripting (XSS) attacks.

---

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Sanitization Profiles](#sanitization-profiles)
- [Usage Examples](#usage-examples)
- [Flask Integration](#flask-integration)
- [Best Practices](#best-practices)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Overview

### What is XSS?

Cross-Site Scripting (XSS) is a security vulnerability where attackers inject malicious scripts into web applications through user input. These scripts execute in victims' browsers, potentially:

- Stealing session cookies
- Capturing keystrokes
- Redirecting to malicious sites
- Defacing the website
- Stealing sensitive data

### Our Solution

We use **Bleach**, a whitelist-based HTML sanitization library that:

- ✅ Removes dangerous HTML tags (`<script>`, `<iframe>`, etc.)
- ✅ Strips malicious attributes (`onclick`, `onerror`, etc.)
- ✅ Validates URL protocols (blocks `javascript:`, `data:`, etc.)
- ✅ Filters CSS properties (prevents CSS-based attacks)
- ✅ Configurable whitelist (multiple security profiles)

---

## Installation

### Dependencies

```bash
# Install Bleach
pip install bleach==6.1.0

# Or install all Phase 1 requirements
pip install -r requirements-phase1.txt
```

### Verify Installation

```python
from backend.security.html_sanitizer import check_bleach_installation

is_installed, message = check_bleach_installation()
print(message)
# Output: "Bleach 6.1.0 is installed and ready"
```

---

## Quick Start

### Basic Usage

```python
from backend.security.html_sanitizer import sanitize_html

# Sanitize user input
user_input = '<p>Hello</p><script>alert("XSS")</script>'
clean_html = sanitize_html(user_input)
print(clean_html)
# Output: '<p>Hello</p>'
```

### Strip All HTML

```python
from backend.security.html_sanitizer import strip_html

html = '<p>Hello <strong>World</strong></p>'
text = strip_html(html)
print(text)
# Output: 'Hello World'
```

### User Input Sanitization

```python
from backend.security.html_sanitizer import sanitize_user_input

# No HTML allowed (default)
text = sanitize_user_input('<script>alert("XSS")</script>Hello')
# Returns: 'alert("XSS")Hello' (HTML stripped)

# HTML allowed (sanitized)
html = sanitize_user_input('<p>Hello</p><script>alert("XSS")</script>', allow_html=True)
# Returns: '<p>Hello</p>' (script removed)
```

---

## Sanitization Profiles

### Strict Profile

**Use for**: Comments, user bios, basic text fields

**Allowed tags**: Basic formatting only (no links)
- `p`, `br`, `strong`, `em`, `b`, `i`, `u`
- `ul`, `ol`, `li`
- `h1`-`h6`, `blockquote`, `code`, `pre`

**Example**:
```python
from backend.security.html_sanitizer import sanitize_html

user_bio = '<p>Software Engineer</p><a href="http://evil.com">Click me</a>'
clean = sanitize_html(user_bio, profile='strict')
# Output: '<p>Software Engineer</p>Click me' (link removed)
```

### Standard Profile (Default)

**Use for**: Blog posts, descriptions, general user content

**Allowed tags**: Basic formatting + links
- All strict tags PLUS
- `a`, `abbr`, `acronym`, `cite`, `span`, `div`

**Allowed attributes**:
- `class`, `id` on all elements
- `href`, `title`, `rel` on links
- `title` on abbreviations

**Features**:
- Automatic `rel="nofollow"` on user links (anti-spam)
- Only `http://`, `https://`, `mailto:`, `ftp://` protocols

**Example**:
```python
content = '''
<p>Check out <a href="https://example.com">my website</a></p>
<a href="javascript:alert('XSS')">Malicious</a>
<img src="x" onerror="alert('XSS')">
'''

clean = sanitize_html(content, profile='standard')
# Output: '<p>Check out <a href="https://example.com" rel="nofollow">my website</a></p>'
# Malicious link and image removed
```

### Rich Profile

**Use for**: Trusted users, admin content, formatted articles

**Allowed tags**: Extended formatting
- All standard tags PLUS
- `table`, `thead`, `tbody`, `tr`, `th`, `td`
- `img`, `hr`, `dl`, `dt`, `dd`
- `sup`, `sub`, `del`, `ins`

**Allowed attributes**:
- `style` attribute (with CSS filtering)
- `src`, `alt`, `width`, `height` on images
- `target` on links
- Table attributes

**Allowed CSS properties**:
- `color`, `background-color`
- `font-size`, `font-weight`, `font-style`
- `text-align`, `text-decoration`
- `margin`, `padding`
- `border`, `border-radius`
- `width`, `height`

**Example**:
```python
article = '''
<p style="color: red;">Important notice</p>
<img src="https://example.com/image.jpg" alt="Example" width="300">
<table>
  <tr><th>Header</th></tr>
  <tr><td>Data</td></tr>
</table>
'''

clean = sanitize_html(article, profile='rich')
# All safe elements preserved, malicious CSS/JS removed
```

### None Profile

**Use for**: Plain text fields (usernames, emails, etc.)

**Behavior**: Strips ALL HTML tags

**Example**:
```python
username = '<script>alert("XSS")</script>john_doe<strong>admin</strong>'
clean = sanitize_html(username, profile='none')
# Output: 'alert("XSS")john_doeadmin'
```

---

## Usage Examples

### Example 1: User Registration

```python
from flask import request, jsonify
from backend.security.html_sanitizer import sanitize_user_input
from backend.schemas import UserRegistrationSchema, validate_request_data

@app.route('/auth/register', methods=['POST'])
def register():
    data = request.get_json()

    # Validate with schema
    is_valid, result = validate_request_data(UserRegistrationSchema, data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': result}), 400

    # Sanitize HTML in fields that might contain user-generated content
    # Note: Username and email should NOT contain HTML (strip it)
    username = sanitize_user_input(result['username'], allow_html=False)
    email = sanitize_user_input(result['email'], allow_html=False)

    # Create user
    user = User(username=username, email=email)
    user.set_password(result['password'])

    db.session.add(user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201
```

### Example 2: User Profile Update

```python
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.security.html_sanitizer import sanitize_html

@app.route('/api/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    data = request.get_json()

    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Sanitize bio (allow basic HTML formatting)
    if 'bio' in data:
        user.bio = sanitize_html(data['bio'], profile='standard')

    # Sanitize display name (no HTML)
    if 'display_name' in data:
        user.display_name = sanitize_html(data['display_name'], profile='none')

    db.session.commit()
    return jsonify({'message': 'Profile updated'}), 200
```

### Example 3: Blog Post Creation

```python
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.security.html_sanitizer import sanitize_html

@app.route('/api/posts', methods=['POST'])
@jwt_required()
def create_post():
    user_id = get_jwt_identity()
    data = request.get_json()

    # Validate required fields
    if not data.get('title') or not data.get('content'):
        return jsonify({'error': 'Title and content required'}), 400

    # Sanitize title (no HTML)
    title = sanitize_html(data['title'], profile='none')

    # Sanitize content based on user role
    user = User.query.get(user_id)
    if user.is_admin:
        # Admins can use rich formatting
        content = sanitize_html(data['content'], profile='rich')
    else:
        # Regular users get standard formatting
        content = sanitize_html(data['content'], profile='standard')

    # Create post
    post = Post(
        title=title,
        content=content,
        author_id=user_id
    )

    db.session.add(post)
    db.session.commit()

    return jsonify({'message': 'Post created', 'id': post.id}), 201
```

### Example 4: Knowledge Node Creation

```python
from flask import request, jsonify
from backend.security.html_sanitizer import sanitize_json_fields
from backend.schemas import KnowledgeNodeCreateSchema, validate_request_data

@app.route('/api/knowledge/nodes', methods=['POST'])
@jwt_required()
def create_knowledge_node():
    data = request.get_json()

    # Validate with schema
    is_valid, result = validate_request_data(KnowledgeNodeCreateSchema, data)
    if not is_valid:
        return jsonify({'error': 'Validation failed', 'details': result}), 400

    # Sanitize HTML fields
    sanitized = sanitize_json_fields(
        result,
        fields=['label', 'description'],
        profile='standard'
    )

    # Create knowledge node
    node = KnowledgeGraphNode(
        node_id=sanitized['node_id'],
        label=sanitized['label'],
        node_type=sanitized['node_type'],
        description=sanitized.get('description', ''),
        data=sanitized.get('data', {})
    )

    db.session.add(node)
    db.session.commit()

    return jsonify({'message': 'Node created', 'id': node.id}), 201
```

### Example 5: Comment System

```python
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.security.html_sanitizer import sanitize_html

@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
@jwt_required()
def create_comment(post_id):
    user_id = get_jwt_identity()
    data = request.get_json()

    # Validate
    if not data.get('content'):
        return jsonify({'error': 'Content required'}), 400

    # Sanitize comment content (strict profile - no links to prevent spam)
    content = sanitize_html(data['content'], profile='strict')

    # Check content length after sanitization
    if len(content.strip()) < 1:
        return jsonify({'error': 'Comment cannot be empty'}), 400

    # Create comment
    comment = Comment(
        content=content,
        post_id=post_id,
        user_id=user_id
    )

    db.session.add(comment)
    db.session.commit()

    return jsonify({'message': 'Comment created', 'id': comment.id}), 201
```

---

## Flask Integration

### Method 1: Decorator (Automatic Sanitization)

```python
from flask import request, jsonify
from backend.security.html_sanitizer import sanitize_request_decorator

@app.route('/api/posts', methods=['POST'])
@sanitize_request_decorator(['title', 'content'], profile='standard')
def create_post():
    data = request.get_json()
    # data['title'] and data['content'] are now sanitized
    # ... create post ...
```

### Method 2: Manual Sanitization

```python
from flask import request, jsonify
from backend.security.html_sanitizer import sanitize_html

@app.route('/api/posts', methods=['POST'])
def create_post():
    data = request.get_json()

    # Manually sanitize specific fields
    title = sanitize_html(data.get('title', ''), profile='none')
    content = sanitize_html(data.get('content', ''), profile='standard')

    # ... create post ...
```

### Method 3: Bulk Field Sanitization

```python
from flask import request, jsonify
from backend.security.html_sanitizer import sanitize_json_fields

@app.route('/api/posts', methods=['POST'])
def create_post():
    data = request.get_json()

    # Sanitize multiple fields at once
    sanitized = sanitize_json_fields(
        data,
        fields=['title', 'content', 'excerpt'],
        profile='standard'
    )

    # ... use sanitized data ...
```

---

## Best Practices

### 1. Always Sanitize User Input

**✅ DO**: Sanitize ALL user-generated content before storing or displaying

```python
# Good
user_bio = sanitize_html(data['bio'], profile='standard')
```

**❌ DON'T**: Trust user input

```python
# Bad - XSS vulnerability!
user_bio = data['bio']  # No sanitization
```

### 2. Choose Appropriate Profile

- **Username, email**: Use `none` (no HTML)
- **Comments, bios**: Use `strict` (basic formatting, no links)
- **Posts, descriptions**: Use `standard` (formatting + links)
- **Admin content**: Use `rich` (full formatting)

### 3. Sanitize on Input, Not Output

**✅ DO**: Sanitize when storing data

```python
# Good - sanitize once on input
post.content = sanitize_html(data['content'], 'standard')
db.session.commit()
```

**❌ DON'T**: Sanitize on every display

```python
# Bad - performance issue, inconsistent
# Template: {{ sanitize_html(post.content) }}
```

### 4. Validate Before Sanitizing

**✅ DO**: Use schema validation first, then sanitize

```python
# Good
is_valid, result = validate_request_data(PostSchema, data)
if not is_valid:
    return error_response(result)

sanitized = sanitize_json_fields(result, ['content'], 'standard')
```

### 5. Consider Content Length After Sanitization

```python
# Check if content is empty after sanitization
content = sanitize_html(data['content'], 'standard')
if len(content.strip()) < 10:
    return jsonify({'error': 'Content too short'}), 400
```

### 6. Log Sanitization Events (Optional)

```python
original_content = data['content']
sanitized_content = sanitize_html(original_content, 'standard')

if original_content != sanitized_content:
    logger.warning(f"XSS attempt blocked from user {user_id}")
```

---

## Testing

### Unit Tests

```python
# tests/test_html_sanitizer.py
import pytest
from backend.security.html_sanitizer import sanitize_html, strip_html

def test_sanitize_removes_script_tags():
    """Test that script tags are removed"""
    html = '<p>Safe</p><script>alert("XSS")</script>'
    clean = sanitize_html(html, 'standard')
    assert '<script>' not in clean
    assert '<p>Safe</p>' in clean

def test_sanitize_removes_event_handlers():
    """Test that event handlers are removed"""
    html = '<a href="#" onclick="alert(\'XSS\')">Click</a>'
    clean = sanitize_html(html, 'standard')
    assert 'onclick' not in clean
    assert '<a href="#">Click</a>' in clean or 'Click' in clean

def test_sanitize_blocks_javascript_protocol():
    """Test that javascript: protocol is blocked"""
    html = '<a href="javascript:alert(\'XSS\')">Click</a>'
    clean = sanitize_html(html, 'standard')
    assert 'javascript:' not in clean.lower()

def test_strip_html_removes_all_tags():
    """Test that strip_html removes all HTML"""
    html = '<p>Hello <strong>World</strong></p>'
    text = strip_html(html)
    assert text == 'Hello World'
    assert '<' not in text

def test_strict_profile_removes_links():
    """Test that strict profile removes links"""
    html = '<p>Text</p><a href="http://example.com">Link</a>'
    clean = sanitize_html(html, 'strict')
    assert '<p>Text</p>' in clean
    assert '<a' not in clean

def test_standard_profile_allows_links():
    """Test that standard profile allows safe links"""
    html = '<a href="https://example.com">Link</a>'
    clean = sanitize_html(html, 'standard')
    assert '<a' in clean
    assert 'https://example.com' in clean
```

### Integration Tests

```python
# tests/test_api_sanitization.py
import pytest
from app import app, db

def test_post_creation_sanitizes_content(client, auth_headers):
    """Test that post creation sanitizes malicious content"""
    response = client.post('/api/posts', json={
        'title': 'Test Post',
        'content': '<p>Safe content</p><script>alert("XSS")</script>'
    }, headers=auth_headers)

    assert response.status_code == 201

    # Verify content was sanitized
    post = Post.query.filter_by(title='Test Post').first()
    assert '<p>Safe content</p>' in post.content
    assert '<script>' not in post.content
```

---

## Troubleshooting

### Issue: Bleach Not Installed

**Error**: `ModuleNotFoundError: No module named 'bleach'`

**Solution**:
```bash
pip install bleach==6.1.0
```

### Issue: Valid HTML Being Removed

**Problem**: Legitimate HTML tags are being stripped

**Solution**: Check if you're using the correct profile

```python
# If links are being removed, use 'standard' instead of 'strict'
clean = sanitize_html(content, 'standard')  # Allows links
# instead of
clean = sanitize_html(content, 'strict')    # No links
```

### Issue: CSS Styles Being Removed

**Problem**: Inline styles are being stripped

**Solution**: Use 'rich' profile for CSS support

```python
# Rich profile allows inline styles (filtered)
clean = sanitize_html(content, 'rich')
```

### Issue: Performance with Large Content

**Problem**: Sanitization is slow for large HTML documents

**Solution**:
1. Sanitize once on input, not output
2. Consider caching sanitized content
3. Limit content length before sanitization

```python
# Limit content length
MAX_CONTENT_LENGTH = 50000  # 50KB
if len(content) > MAX_CONTENT_LENGTH:
    return error_response('Content too large')

# Sanitize and cache
sanitized = sanitize_html(content, 'standard')
```

---

## Security Notes

### What Bleach Protects Against

- ✅ XSS via `<script>` tags
- ✅ XSS via event handlers (`onclick`, `onerror`, etc.)
- ✅ XSS via `javascript:` protocol
- ✅ XSS via `data:` URLs
- ✅ XSS via malicious CSS
- ✅ HTML injection
- ✅ Iframe embedding

### What Bleach Does NOT Protect Against

- ❌ SQL injection (use parameterized queries)
- ❌ CSRF (use CSRF tokens)
- ❌ Command injection (validate all inputs)
- ❌ Path traversal (validate file paths)
- ❌ Authentication bypass (use proper auth)

### Defense in Depth

HTML sanitization is ONE layer of security. Also implement:

1. **Content Security Policy (CSP)** - Already configured in `security_headers.py`
2. **Input Validation** - Using Marshmallow schemas
3. **Output Encoding** - Flask/Jinja2 auto-escaping
4. **Rate Limiting** - Already configured
5. **HTTPS Only** - Enforce in production

---

## Quick Reference

```python
from backend.security.html_sanitizer import (
    sanitize_html,        # Main sanitization function
    strip_html,           # Remove all HTML
    sanitize_user_input,  # Convenience for user input
    sanitize_json_fields, # Bulk field sanitization
)

# Basic sanitization
clean = sanitize_html(user_input, profile='standard')

# Strip all HTML
text = strip_html(user_input)

# User input (auto-detect HTML)
safe = sanitize_user_input(user_input, allow_html=True)

# Bulk sanitization
data = sanitize_json_fields(data, ['title', 'content'], 'standard')

# Profiles: 'strict', 'standard', 'rich', 'none'
```

---

**XSS Protection Complete! 🔒**

All user-generated content should now be sanitized before storage or display.

See [PHASE_1_STATUS.md](PHASE_1_STATUS.md) for next implementation steps.
