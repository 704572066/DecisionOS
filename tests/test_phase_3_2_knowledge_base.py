import os
import shutil
import tempfile
from pathlib import Path

db_path = os.path.join(tempfile.gettempdir(), "decisionos_phase32_e2e.db")
storage_path = os.path.join(tempfile.gettempdir(), "decisionos_phase32_knowledge")
shutil.rmtree(storage_path, ignore_errors=True)
try:
    os.remove(db_path)
except FileNotFoundError:
    pass
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
os.environ["KNOWLEDGE_STORAGE_DIR"] = storage_path
os.environ["OPENAI_API_KEY"] = ""
os.environ["EMBEDDING_API_KEY"] = ""

from fastapi.testclient import TestClient

from app.main import app


def register(client, email):
    response = client.post("/api/auth/register", json={
        "email": email, "password": "password123", "username": email.split("@")[0],
    })
    assert response.status_code == 201, response.text


def run():
    with TestClient(app) as owner, TestClient(app) as other:
        register(owner, "knowledge-owner@example.com")
        register(other, "knowledge-other@example.com")
        project_id = owner.post("/api/projects", json={"name": "Knowledge E2E", "businessGoal": "test"}).json()["id"]

        uploaded = owner.post(
            "/api/knowledge",
            data={"objectType": "policy", "projectId": ""},
            files={"file": ("margin-policy.md", b"POLICY_18 gross margin must be at least 18 percent.", "text/markdown")},
        )
        assert uploaded.status_code == 202, uploaded.text
        source_id = uploaded.json()["id"]

        detail = owner.get(f"/api/knowledge/{source_id}")
        assert detail.status_code == 200, detail.text
        assert detail.json()["status"] == "ready"
        assert detail.json()["itemCount"] == 1
        assert other.get(f"/api/knowledge/{source_id}").status_code == 404
        assert other.delete(f"/api/knowledge/{source_id}").status_code == 404

        result = owner.post("/api/retrieval/search", json={
            "projectId": project_id, "text": "POLICY_18", "topK": 5,
        })
        assert result.status_code == 200, result.text
        assert "POLICY_18" in str(result.json()["results"])

        assert owner.delete(f"/api/knowledge/{source_id}").status_code == 204
        result = owner.post("/api/retrieval/search", json={
            "projectId": project_id, "text": "POLICY_18", "topK": 5,
        })
        assert "POLICY_18" not in str(result.json()["results"])
        assert not list(Path(storage_path).rglob("*.*"))
    print("PHASE 3.2 KNOWLEDGE BASE: OK")


if __name__ == "__main__":
    run()

