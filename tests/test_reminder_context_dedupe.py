
from types import SimpleNamespace

def make_context(text, facts):
    return SimpleNamespace(
        cleanTranscriptWindow=text,
        facts=[
            SimpleNamespace(normalizedValue=value, text=value)
            for value in facts
        ],
    )

def test_same_context_same_key():
    from app.api.audio_ws import reminder_context_key
    a = make_context(
        "客户要求整体价格下降18%，并希望付款周期延长到180天。",
        ["18%", "180天"],
    )
    b = make_context(
        " 客户要求整体价格下降18%，并希望付款周期延长到180天。 ",
        ["180天", "18%"],
    )
    assert reminder_context_key(a) == reminder_context_key(b)

def test_changed_fact_new_key():
    from app.api.audio_ws import reminder_context_key
    a = make_context("客户要求整体价格下降18%。", ["18%"])
    b = make_context("客户要求整体价格下降12%。", ["12%"])
    assert reminder_context_key(a) != reminder_context_key(b)
