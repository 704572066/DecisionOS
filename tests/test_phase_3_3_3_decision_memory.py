import os
import tempfile

db_path = os.path.join(tempfile.gettempdir(), "decisionos_phase333_e2e.db")
try:
    os.remove(db_path)
except FileNotFoundError:
    pass
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
os.environ["OPENAI_API_KEY"] = ""
os.environ["EMBEDDING_API_KEY"] = ""

from fastapi.testclient import TestClient
from app.main import app


def register(client, email):
    response = client.post("/api/auth/register", json={"email": email, "password": "password123", "username": email.split("@")[0]})
    assert response.status_code == 201, response.text


def finalized_summary(client, text, title):
    meeting_id = client.post("/api/meetings", json={"title": title}).json()["id"]
    assert client.post(f"/api/meetings/{meeting_id}/transcript", json={"text": text}).status_code == 200
    assert client.post(f"/api/meeting-history/{meeting_id}/end").status_code == 200
    assert client.post(f"/api/meeting-history/{meeting_id}/finalize").status_code == 200
    summary = client.post(f"/api/meeting-history/{meeting_id}/summary")
    assert summary.status_code == 200, summary.text
    return meeting_id, summary.json()


def run():
    with TestClient(app) as owner, TestClient(app) as other:
        register(owner, "memory-owner@example.com")
        register(other, "memory-other@example.com")

        meeting_a, summary_a = finalized_summary(owner, "最终决定按10%折扣、90天付款周期推进签约。", "Meeting A")
        assert len(summary_a["decisions"]) == 1
        memories_a = owner.get(f"/api/decision-memories?meetingId={meeting_a}").json()
        assert len(memories_a) == 1 and memories_a[0]["status"] == "active"
        assert memories_a[0]["sourceIds"] and memories_a[0]["evidence"]
        assert memories_a[0]["sourceMeetingId"] == meeting_a

        meeting_b = owner.post("/api/meetings", json={"title": "Meeting B"}).json()["id"]
        owner.post(f"/api/meetings/{meeting_b}/transcript", json={"text": "客户提出12%折扣和180天付款周期。"})
        owner.post(f"/api/meetings/{meeting_b}/analyze")
        board = owner.post(f"/api/decision-board/{meeting_b}/refresh").json()
        assert any(row["type"] == "decision_memory" and meeting_a in row["summary"] for row in board["evidence"])
        assert any("历史会议决策" in row["title"] for row in board["reasoning"]["findings"]), board["reasoning"]
        dialogue = owner.post(f"/api/dialogue/{meeting_b}", json={"text": "你为什么这么判断？"})
        assert dialogue.status_code == 200 and meeting_a in dialogue.json()["answer"]
        assert memories_a[0]["id"] in dialogue.json()["sourceIds"]

        assert other.get("/api/decision-memories").json() == []
        assert other.post(f"/api/decision-memories/{memories_a[0]['id']}/revoke").status_code == 404
        other_meeting = other.post("/api/meetings", json={"title": "隔离验证"}).json()["id"]
        other.post(f"/api/meetings/{other_meeting}/transcript", json={"text": "客户提出12%折扣和180天付款周期。"})
        other.post(f"/api/meetings/{other_meeting}/analyze")
        other_board = other.post(f"/api/decision-board/{other_meeting}/refresh").json()
        assert not any(row["type"] == "decision_memory" for row in other_board["evidence"])

        meeting_c, _ = finalized_summary(owner, "最终决定将折扣上限调整为12%，付款周期调整为120天，按此推进签约。", "Meeting C")
        all_memories = owner.get("/api/decision-memories").json()
        memory_c = next(row for row in all_memories if row["sourceMeetingId"] == meeting_c)
        memory_a = next(row for row in all_memories if row["sourceMeetingId"] == meeting_a)
        assert memory_c["status"] == "active" and memory_c["supersedesId"] == memory_a["id"]
        assert memory_a["status"] == "superseded"

        meeting_d = owner.post("/api/meetings", json={"title": "Meeting D"}).json()["id"]
        owner.post(f"/api/meetings/{meeting_d}/transcript", json={"text": "讨论12%折扣和120天付款周期。"})
        owner.post(f"/api/meetings/{meeting_d}/analyze")
        board_d = owner.post(f"/api/decision-board/{meeting_d}/refresh").json()
        ids = {row["id"] for row in board_d["evidence"] if row["type"] == "decision_memory"}
        assert memory_c["id"] in ids and memory_a["id"] not in ids
    print("PHASE 3.3.3 DECISION MEMORY: OK")


if __name__ == "__main__":
    run()

