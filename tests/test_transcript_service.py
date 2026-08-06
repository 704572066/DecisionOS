from app.services.transcript_service import (
    normalize_transcript_text,
    transcript_fingerprint,
)


def test_normalize_transcript_text():
    assert normalize_transcript_text("  客户   希望付款  ") == "客户 希望付款"


def test_fingerprint_ignores_common_punctuation():
    assert transcript_fingerprint("客户希望付款。") == transcript_fingerprint(
        "客户希望付款"
    )
