from datetime import datetime, timezone

from app.decision_board.engine import decision_board_engine
from app.runtime.models import RuntimeState


def test_resolved_old_payment_risk_is_removed():
    state = RuntimeState(
        meetingId="m1",
        projectId="p1",
        contextId="c1",
        objective="完成签约",
        canonicalContext="客户付款周期调整到90天。",
        topics=["付款"],
        facts=[{"normalizedValue": "90天"}],
        decisionFacts={"paymentTermDays": 90},
        resolvedRiskKeys=["payment_term"],
        reminders=[
            {
                "type": "risk",
                "title": "180天付款周期存在风险",
                "summary": "客户要求付款周期180天，存在回款风险。",
                "confidence": .95,
                "sources": [],
            }
        ],
        updatedAt=datetime.now(timezone.utc),
    )
    board = decision_board_engine.build(state)
    assert not board.risks
    assert board.currentConditions["paymentTermDays"] == 90


def test_claim_guard_does_not_equate_discount_and_margin():
    state = RuntimeState(
        meetingId="m1",
        projectId="p1",
        contextId="c1",
        objective="保证利润率",
        canonicalContext="客户要求降价18%。",
        topics=["价格"],
        facts=[{"normalizedValue": "18%"}],
        reminders=[
            {
                "type": "risk",
                "title": "18%降价突破18%毛利率底线",
                "summary": "18%降价与18%毛利率直接冲突。",
                "confidence": .95,
                "sources": [],
            }
        ],
        updatedAt=datetime.now(timezone.utc),
    )
    board = decision_board_engine.build(state)
    assert board.risks
    assert "不能直接等同" in board.risks[0].summary
