from backend.utils.error_normalization import normalize_public_error_message


def test_public_error_normalization_never_returns_raw_exception_details():
    raw = "database permission denied at C:/private; password=super-secret"

    result = normalize_public_error_message(raw, "Request failed")

    assert result == "Permission denied"
    assert "database" not in result
    assert "private" not in result
    assert "super-secret" not in result


def test_custom_safe_fragments_return_only_the_canonical_fragment():
    raw = "provider rate limited: token=super-secret; upstream=https://internal"

    result = normalize_public_error_message(
        raw,
        "Provider request failed",
        safe_fragments=("rate limited",),
    )

    assert result == "rate limited"
    assert "super-secret" not in result
    assert "internal" not in result
