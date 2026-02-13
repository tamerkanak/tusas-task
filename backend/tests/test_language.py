from __future__ import annotations

from backend.app.services.documents import DocumentService


def test_detect_language_returns_unknown_for_short_text() -> None:
    assert DocumentService._detect_language("Hi") == "unknown"


def test_detect_language_detects_english() -> None:
    text = "This document is written in English and it should be detected correctly."
    assert DocumentService._detect_language(text) == "en"


def test_detect_language_detects_turkish_with_diacritics() -> None:
    text = (
        "Bu bir Turkce test cumlesidir: "
        "\u00e7\u011f\u0131\u00f6\u015f\u00fc karakterleri burada geciyor."
    )
    assert DocumentService._detect_language(text) == "tr"

