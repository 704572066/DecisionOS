from app.core.config import settings
from app.intelligence.llm import llm_provider


def test_realtime_reminder_thinking_disabled():
    original = getattr(settings, 'reminder_enable_thinking', False)
    try:
        settings.reminder_enable_thinking = False
        body = llm_provider._body('system', 'user', stream=True)
        assert body['stream'] is True
        assert body['enable_thinking'] is False
    finally:
        settings.reminder_enable_thinking = original
