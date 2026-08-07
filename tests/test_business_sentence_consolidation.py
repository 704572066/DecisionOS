from app.context.cleaner import clean_transcript


def test_consolidates_price_and_payment_sentences():
    raw = """
客户要求整体价格下降18%
并希望付款周期延长到180天
客户要求整体价格下降18%
并希望付款周期延长到180天
"""
    result = clean_transcript(raw)
    assert result.clean_text == (
        "客户要求整体价格下降18%，并希望付款周期延长到180天。"
    )
    assert result.consolidated_sentences >= 1


def test_fixes_observed_percentage_noise():
    result = clean_transcript("客户要求整体价格下降100分18%")
    assert "100分" not in result.clean_text
    assert "18%" in result.clean_text


def test_filters_low_information_conversation():
    raw = """
你不要觉得你一买
客户要求整体价格下降18%
"""
    result = clean_transcript(raw)
    assert "你不要觉得你一买" not in result.clean_text
    assert "客户要求整体价格下降18%" in result.clean_text


def test_drops_incomplete_fragments_when_complete_sentence_exists():
    raw = """
下降18%
客户要求整体价格
客户要求整体价格下降18%
"""
    result = clean_transcript(raw)
    assert result.clean_text == "客户要求整体价格下降18%。"
