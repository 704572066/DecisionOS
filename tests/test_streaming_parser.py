from app.intelligence.streaming import StructuredReminderStreamParser

def test_streaming_parser_exposes_partial_fields():
    parser = StructuredReminderStreamParser("r1")
    updates = parser.feed('{"reminders":[{"type":"risk","title":"价格与')
    assert any(x.field == "title" and x.accumulated == "价格与" for x in updates)

    updates = parser.feed('账期风险","summary":"客户要求')
    assert any(x.field == "title" and x.accumulated == "价格与账期风险" for x in updates)
    assert any(x.field == "summary" for x in updates)
