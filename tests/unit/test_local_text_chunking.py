import re

import pytest

from backend.services.text_chunking import split_text


def test_sentence_chunks_preserve_text_and_are_repeatable():
    text = "One short sentence. Another sentence follows! Final sentence here?"
    chunks = split_text(text, chunk_size=8, overlap=0)
    assert chunks == split_text(text, chunk_size=8, overlap=0)
    assert " ".join(chunks) == text
    assert all(len(re.findall(r"\w{1,64}|[^\w\s]", chunk)) <= 8 for chunk in chunks)


def test_long_unbroken_input_is_bounded_and_not_dropped():
    text = "a" * 10_000
    chunks = split_text(text, chunk_size=10, overlap=0)
    assert "".join(chunks) == text
    assert max(map(len, chunks)) <= 640


def test_overlap_keeps_context_and_makes_forward_progress():
    assert split_text("one two three four five six", chunk_size=4, overlap=2) == [
        "one two three four",
        "three four five six",
    ]
    assert split_text(" \n\t") == []


@pytest.mark.parametrize("size,overlap", [(0, 0), (4, -1), (4, 4)])
def test_invalid_bounds_fail_explicitly(size, overlap):
    with pytest.raises(ValueError):
        split_text("text", size, overlap)
