from app.decision.candidate_service import DecisionCandidateService

def test_statement_prefers_suggestion():
    service=DecisionCandidateService()
    reminder={"summary":"客户要求降价18%。","suggestion":"优先缩短付款周期。"}
    assert service._statement(reminder)=="优先缩短付款周期。"

def test_risk_is_preserved():
    service=DecisionCandidateService()
    assert service._risks({"type":"risk","summary":"180天付款周期风险较高。"})==["180天付款周期风险较高。"]
