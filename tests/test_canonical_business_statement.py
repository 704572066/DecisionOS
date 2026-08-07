from app.context.canonicalizer import canonicalize_business_statements


def test_collapses_price_and_payment_variants():
    source = [
        "客户要求整体价格下降18%，并希望付款周期延长到180天。",
        "客户要求整体价格下降18%并希望付款周期延长到180天，客户要求整体价格下降18%并希望客户整体价格。",
        "下降18%，客户要求整体价格。",
    ]
    result = canonicalize_business_statements(source)
    assert result.statements == ["客户要求整体价格下降18%，并希望付款周期延长到180天。"]


def test_keeps_unrelated_delivery_statement():
    source = [
        "客户要求整体价格下降18%，并希望付款周期延长到180天。",
        "客户要求9月30日前完成交付。",
    ]
    result = canonicalize_business_statements(source)
    assert len(result.statements) == 2
    assert any("9月30日前完成交付" in item for item in result.statements)
