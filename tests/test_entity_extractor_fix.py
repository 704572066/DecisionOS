from app.context.extractor import entities

def test_no_false_customer():
    assert all(x.name!="电影希望客户" for x in entities("电影希望客户整体价格下降18%。"))

def test_named_customer():
    assert any(x.name=="客户A" for x in entities("客户A要求付款周期延长到180天。"))
