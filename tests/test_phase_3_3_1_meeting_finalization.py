import os
import tempfile

db_path = os.path.join(tempfile.gettempdir(), "decisionos_phase331_e2e.db")
try:
    os.remove(db_path)
except FileNotFoundError:
    pass
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
os.environ["OPENAI_API_KEY"] = ""
os.environ["EMBEDDING_API_KEY"] = ""

from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models.entities import MeetingDialogueTurn


def register(client, email):
    response = client.post("/api/auth/register", json={
        "email": email, "password": "password123", "username": email.split("@")[0],
    })
    assert response.status_code == 201, response.text


def run():
    with TestClient(app) as owner, TestClient(app) as other:
        register(owner, "history-owner@example.com")
        register(other, "history-other@example.com")
        created = owner.post("/api/meetings", json={"title": "付款条件确认"})
        assert created.status_code == 200, created.text
        meeting_id = created.json()["id"]

        transcript = owner.post(f"/api/meetings/{meeting_id}/transcript", json={
            "text": "最终确认最多接受10%折扣，付款周期必须控制在90天以内。",
        })
        assert transcript.status_code == 200, transcript.text
        board = owner.post(f"/api/decision-board/{meeting_id}/refresh")
        assert board.status_code == 200, board.text
        db = SessionLocal()
        workspace_id = owner.get("/api/auth/me").json()["workspace"]["id"]
        db.add_all([
            MeetingDialogueTurn(workspace_id=workspace_id, meeting_id=meeting_id, role="user", content="当前确认的条件是什么？"),
            MeetingDialogueTurn(workspace_id=workspace_id, meeting_id=meeting_id, role="assistant", content="折扣10%，账期90天。"),
        ])
        db.commit(); db.close()

        ended = owner.post(f"/api/meeting-history/{meeting_id}/end")
        assert ended.status_code == 200 and ended.json()["status"] == "ended"
        assert owner.post(f"/api/meetings/{meeting_id}/transcript", json={"text": "不得写入"}).status_code == 409
        assert owner.post(f"/api/dialogue/{meeting_id}", json={"text": "不得继续"}).status_code == 409

        finalized = owner.post(f"/api/meeting-history/{meeting_id}/finalize")
        assert finalized.status_code == 200, finalized.text
        frozen = finalized.json()["snapshot"]
        assert frozen["meeting"]["status"] == "finalized"
        assert "10%" in frozen["transcript"] and "90天" in frozen["transcript"]
        assert len(frozen["dialogue"]) == 2

        again = owner.post(f"/api/meeting-history/{meeting_id}/finalize")
        assert again.status_code == 200 and again.json()["snapshot"] == frozen
        detail = owner.get(f"/api/meeting-history/{meeting_id}")
        assert detail.status_code == 200 and detail.json()["snapshot"] == frozen
        owner_history = owner.get("/api/meeting-history")
        assert owner_history.headers["cache-control"] == "private, no-store"
        assert any(item["id"] == meeting_id for item in owner_history.json())

        other_history = other.get("/api/meeting-history")
        assert other_history.status_code == 200 and other_history.json() == []
        assert other_history.headers["cache-control"] == "private, no-store"
        assert other.get(f"/api/meeting-history/{meeting_id}").status_code == 404
        assert other.post(f"/api/meeting-history/{meeting_id}/end").status_code == 404
    print("PHASE 3.3.1 MEETING FINALIZATION: OK")


if __name__ == "__main__":
    run()

