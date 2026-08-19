import os
import tempfile

db_path=os.path.join(tempfile.gettempdir(),"decisionos_phase31_e2e.db")
try: os.remove(db_path)
except FileNotFoundError: pass
os.environ["DATABASE_URL"]=f"sqlite:///{db_path}"
os.environ["OPENAI_API_KEY"]=""
os.environ["EMBEDDING_API_KEY"]=""

from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models.entities import KnowledgeItem

def register(client,email):
    response=client.post("/api/auth/register",json={"email":email,"password":"password123","username":email.split("@")[0]})
    assert response.status_code==201,response.text
    return response.json()

def run():
    with TestClient(app) as a, TestClient(app) as b:
        ia=register(a,"a@example.com"); ib=register(b,"b@example.com")
        assert ia["workspace"]["id"]!=ib["workspace"]["id"]
        pa=a.get("/api/projects").json()[0]["id"]
        pb=b.get("/api/projects").json()[0]["id"]
        ma=a.post("/api/meetings",json={"title":"A Meeting"}).json()["id"]
        mb=b.post("/api/meetings",json={"title":"B Meeting"}).json()["id"]
        assert {x["id"] for x in a.get("/api/projects").json()}=={pa}
        assert {x["id"] for x in b.get("/api/projects").json()}=={pb}
        assert a.get(f"/api/meetings/{mb}").status_code==404
        assert b.get(f"/api/decision-board/{ma}").status_code==404
        assert b.post("/api/meetings",json={"projectId":pa,"title":"attack"}).status_code==404
        db=SessionLocal()
        db.add_all([
            KnowledgeItem(workspace_id=ia["workspace"]["id"],project_id=pa,object_type="policy",title="A only",content="A_SECRET_MARGIN_POLICY",source_type="policy"),
            KnowledgeItem(workspace_id=ib["workspace"]["id"],project_id=pb,object_type="policy",title="B only",content="B_SECRET_PAYMENT_POLICY",source_type="policy"),
        ]); db.commit(); db.close()
        ra=a.post("/api/retrieval/search",json={"projectId":pa,"text":"B_SECRET_PAYMENT_POLICY A_SECRET_MARGIN_POLICY"})
        assert ra.status_code==200,ra.text
        serialized=str(ra.json()["results"])
        assert "A_SECRET_MARGIN_POLICY" in serialized
        assert "B_SECRET_PAYMENT_POLICY" not in serialized
        assert a.post("/api/retrieval/search",json={"projectId":pb,"text":"B_SECRET_PAYMENT_POLICY"}).status_code==404
        empty_board=a.get(f"/api/decision-board/{ma}")
        assert empty_board.status_code==200 and empty_board.json()["evidence"]==[]
        a.post("/api/auth/logout")
        assert a.get("/api/projects").status_code==401
    print("PHASE 3.1 PERSONAL WORKSPACE ISOLATION: OK")

if __name__=="__main__": run()

