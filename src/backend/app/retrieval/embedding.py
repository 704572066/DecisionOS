import httpx
from dataclasses import dataclass
from app.core.config import settings

@dataclass(slots=True)
class EmbeddingResult:
    vector:list[float]
    model:str

class EmbeddingProvider:
    @property
    def enabled(self):
        return bool(getattr(settings,"embedding_base_url","") and getattr(settings,"embedding_api_key","") and getattr(settings,"embedding_model",""))
    async def embed_many(self,texts):
        if not texts or not self.enabled: return []
        dim=int(getattr(settings,"embedding_dimensions",1536))
        body={"model":settings.embedding_model,"input":texts,"encoding_format":"float"}
        if getattr(settings,"embedding_send_dimensions",False): body["dimensions"]=dim
        async with httpx.AsyncClient(timeout=float(getattr(settings,"embedding_timeout_seconds",20))) as c:
            r=await c.post(settings.embedding_base_url.rstrip("/")+"/embeddings",headers={"Authorization":"Bearer "+settings.embedding_api_key},json=body)
            r.raise_for_status(); payload=r.json()
        rows=sorted(payload["data"],key=lambda x:x["index"])
        out=[]
        for row in rows:
            v=[float(x) for x in row["embedding"]]
            if len(v)!=dim: raise ValueError(f"Embedding dimensions mismatch: expected {dim}, got {len(v)}")
            out.append(EmbeddingResult(v,payload.get("model") or settings.embedding_model))
        return out
    async def embed_one(self,text):
        rows=await self.embed_many([text]); return rows[0] if rows else None

embedding_provider=EmbeddingProvider()
