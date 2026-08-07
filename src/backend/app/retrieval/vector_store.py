from sqlalchemy import text
from app.retrieval.models import RetrievalCandidate

def literal(v): return "["+",".join(f"{x:.8f}" for x in v)+"]"

def vector_search(db,project_id,query_vector,limit=30):
    rows=db.execute(text("""
SELECT id,object_type,source_id,source_type,title,content,
1-(embedding <=> CAST(:embedding AS vector)) similarity
FROM knowledge_items
WHERE project_id=:project_id AND embedding IS NOT NULL
ORDER BY embedding <=> CAST(:embedding AS vector)
LIMIT :limit
"""),{"project_id":project_id,"embedding":literal(query_vector),"limit":limit}).mappings().all()
    out=[]
    for rank,r in enumerate(rows,1):
        s=max(0,min(1,float(r["similarity"] or 0)))
        out.append(RetrievalCandidate(r["id"],r["object_type"],r["source_id"] or "",r["source_type"] or "",r["title"],r["content"],vector_score=s,vector_rank=rank))
    return out

def coverage(db,project_id=None):
    where="WHERE project_id=:project_id" if project_id else ""
    row=db.execute(text(f"SELECT COUNT(*) total,COUNT(embedding) embedded FROM knowledge_items {where}"),({"project_id":project_id} if project_id else {})).mappings().one()
    total=int(row["total"]); embedded=int(row["embedded"])
    return {"total":total,"embedded":embedded,"coverage":round(embedded/total,4) if total else 1}
