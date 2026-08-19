import os
import tempfile

db_path = os.path.join(tempfile.gettempdir(), "decisionos_phase332_e2e.db")
try:
    os.remove(db_path)
except FileNotFoundError:
    pass
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
os.environ["OPENAI_API_KEY"] = ""
os.environ["EMBEDDING_API_KEY"] = ""

from fastapi.testclient import TestClient

from app.main import app
from app.meetings.summary_context import build_summary_context
from app.meetings.summary_governance import summary_governance
from app.meetings.summary_models import SummaryCandidate, SummaryItemCandidate


def register(client, email):
    response = client.post("/api/auth/register", json={"email": email, "password": "password123", "username": email.split("@")[0]})
    assert response.status_code == 201, response.text


def governance_acceptance():
    snapshot = {"segments": [
        {"id": "s-request", "sequence": 1, "text": "客户只接受10%折扣。"},
        {"id": "s-reject", "sequence": 2, "text": "客户拒绝15%方案。"},
        {"id": "s-decision", "sequence": 3, "text": "好，就按10%签，付款周期90天。"},
    ], "findings": [{"id": "f-margin", "title": "毛利率待确认", "summary": "10%折扣后的实际毛利率是否满足要求", "status": "open"}]}
    context = build_summary_context("meeting-governance", snapshot)
    without_decision = SummaryCandidate(
        summary="谈判仍未形成决定",
        keyFacts=[SummaryItemCandidate(text="客户只接受10%折扣", sourceIds=["s-request"])],
        decisions=[SummaryItemCandidate(text="按10%折扣签约", sourceIds=["s-request"])],
        openIssues=[SummaryItemCandidate(text="实际毛利率是否满足要求", sourceIds=["f-margin"])],
    )
    governed = summary_governance.validate(context, without_decision, extraction_mode="test")
    assert governed.decisions == []
    assert governed.keyFacts[0].text == "客户只接受10%折扣"
    assert governed.openIssues[0].text == "实际毛利率是否满足要求"

    explicit = SummaryCandidate(summary="形成明确决定", decisions=[SummaryItemCandidate(
        text="按10%折扣、90天付款周期推进签约", sourceIds=["s-decision"],
    )])
    governed = summary_governance.validate(context, explicit, extraction_mode="test")
    assert len(governed.decisions) == 1
    assert governed.evidence[0].sourceId == "s-decision"


def api_acceptance():
    with TestClient(app) as owner, TestClient(app) as other:
        register(owner, "summary-owner@example.com")
        register(other, "summary-other@example.com")
        meeting_id = owner.post("/api/meetings", json={"title": "总结验收"}).json()["id"]
        assert owner.post(f"/api/meeting-history/{meeting_id}/summary").status_code == 409
        owner.post(f"/api/meetings/{meeting_id}/transcript", json={"text": "客户只接受10%折扣。"})
        owner.post(f"/api/meetings/{meeting_id}/transcript", json={"text": "好，就按10%签，付款周期90天。"})
        owner.post(f"/api/meeting-history/{meeting_id}/end")
        owner.post(f"/api/meeting-history/{meeting_id}/finalize")
        created = owner.post(f"/api/meeting-history/{meeting_id}/summary")
        assert created.status_code == 200, created.text
        assert len(created.json()["decisions"]) == 1
        memories = owner.get(f"/api/decision-memories?meetingId={meeting_id}")
        assert memories.status_code == 200 and len(memories.json()) == 1
        assert owner.get(f"/api/meeting-history/{meeting_id}/summary").json() == created.json()
        assert other.get(f"/api/meeting-history/{meeting_id}/summary").status_code == 404
        assert other.post(f"/api/meeting-history/{meeting_id}/summary").status_code == 404


if __name__ == "__main__":
    governance_acceptance()
    api_acceptance()
    print("PHASE 3.3.2 MEETING SUMMARY: OK")

