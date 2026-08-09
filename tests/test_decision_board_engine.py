from datetime import datetime,timezone
from app.decision_board.engine import decision_board_engine
from app.runtime.models import RuntimeState
def test_board_is_bounded_and_decision_oriented():
    s=RuntimeState(meetingId="m",projectId="p",contextId="c",objective="在保证利润率的前提下完成签约",canonicalContext="客户要求降价18%，付款180天。",topics=["价格","付款"],facts=[{"text":"18%"},{"text":"180天"}],rerankedEvidence=[{"objectId":"policy","sourceType":"policy","title":"利润率规则","rerankScore":1.0},{"objectId":"decision","sourceType":"decision","title":"历史决策","rerankScore":.95}],reminders=[{"type":"risk","title":"价格与账期风险","summary":"需重新评估","suggestion":"优先缩短付款周期","confidence":.92,"sources":[{"id":"policy"}]}],updatedAt=datetime.now(timezone.utc))
    b=decision_board_engine.build(s)
    assert b.status=="negotiating" and len(b.risks)<=3 and len(b.actions)<=3 and len(b.todos)<=5
