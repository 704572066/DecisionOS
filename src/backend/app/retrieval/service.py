import logging,time
from app.retrieval.embedding import embedding_provider
from app.retrieval.keyword import keyword_search
from app.retrieval.vector_store import vector_search
from app.retrieval.fusion import fuse_candidates
logger=logging.getLogger("decisionos.retrieval")
class HybridRetriever:
    async def search(self,db,query):
        start=time.perf_counter(); ks=time.perf_counter()
        kw=keyword_search(db,query,max(30,query.top_k*4)); kms=(time.perf_counter()-ks)*1000
        vec=[]; vms=0; error=None
        if embedding_provider.enabled and query.text.strip():
            try:
                vs=time.perf_counter(); e=await embedding_provider.embed_one(query.text)
                if e: vec=vector_search(db,query.project_id,e.vector,max(30,query.top_k*4))
                vms=(time.perf_counter()-vs)*1000
            except Exception as exc:
                error=str(exc); logger.exception("vector retrieval failed")
        if vec:
            final=fuse_candidates(kw,vec,query.top_k); mode="hybrid"
        else:
            final=kw[:query.top_k]; mode="keyword"
            for x in final: x.hybrid_score=x.keyword_score
        return {"mode":mode,"query":query.text,"results":[x.as_dict() for x in final],"diagnostics":{"keywordCandidates":len(kw),"vectorCandidates":len(vec),"vectorConfigured":embedding_provider.enabled,"vectorError":error,"keywordMs":round(kms,2),"vectorMs":round(vms,2),"totalMs":round((time.perf_counter()-start)*1000,2)}}
hybrid_retriever=HybridRetriever()
