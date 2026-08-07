from app.context.cleaner import clean_transcript

def test_cleaner():
    raw="客户要求整体价格下降18%\n并希望付款周期延长到180天\n客户要求整体价格下降18%\n并希望副感周期延长到180天\n然后\n你好"
    result=clean_transcript(raw)
    assert result.clean_text.count("客户要求整体价格下降18%")==1
    assert result.clean_text.count("付款周期延长到180天")==1
    assert "副感周期" not in result.clean_text
    assert "你好" not in result.clean_text
