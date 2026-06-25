from unittest.mock import patch

import backend.security.sanitizer as sanitizer_module


def test_html_sanitizer_core_paths():
    html = "<script>alert(1)</script><p>safe</p>"
    cleaned = sanitizer_module.HTMLSanitizer.sanitize(html)
    assert "<script>" not in cleaned
    assert "safe" in cleaned

    strict = sanitizer_module.HTMLSanitizer.sanitize_strict("<b>hello</b>")
    assert "<b>" not in strict
    assert "hello" in strict

    text = sanitizer_module.HTMLSanitizer.sanitize_text("<i>plain</i>")
    assert "<i>" not in text
    assert "plain" in text

    linked = sanitizer_module.HTMLSanitizer.linkify("visit https://example.com")
    assert "href" in linked

    form_data = {
        "title": "<b>x</b>",
        "tags": ["<i>a</i>", "b"],
        "count": 3,
    }
    sanitized_form = sanitizer_module.sanitize_form_data(form_data, ["title", "tags"])
    assert sanitized_form["title"] == "x"
    assert sanitized_form["tags"][0] == "a"
    assert sanitized_form["count"] == 3

    sanitized_json = sanitizer_module.sanitize_json_data({"body": "<p>ok</p>"}, ["body"])
    assert sanitized_json["body"] == "ok"

    assert sanitizer_module.sanitize_html("<b>ok</b>", strict=False) == "<b>ok</b>"
    assert sanitizer_module.sanitize_html("<b>ok</b>", strict=True) == "ok"
    assert sanitizer_module.sanitize_text("hello") == "hello"
    assert sanitizer_module.linkify_text("https://example.com")


def test_html_sanitizer_error_paths():
    with patch.object(sanitizer_module.bleach, "clean", side_effect=[RuntimeError("clean fail"), ""]):
        assert sanitizer_module.HTMLSanitizer.sanitize("<b>x</b>") == ""

    with patch.object(sanitizer_module.bleach, "clean", side_effect=RuntimeError("clean fail")):
        assert sanitizer_module.HTMLSanitizer.sanitize_text("<b>x</b>") == ""

    with patch.object(sanitizer_module.bleach, "linkify", side_effect=RuntimeError("link fail")):
        text = "https://example.com"
        assert sanitizer_module.HTMLSanitizer.linkify(text) == text
