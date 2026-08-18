import re
from collections import Counter
from sqlalchemy import or_, select
from app.models.entities import KnowledgeItem
from app.retrieval.models import RetrievalCandidate

TOKEN=re.compile(r"[\u4e00-\u9fff]{2,10}|[A-Za-z0-9]+(?:\.[0-9]+)?%?")
BOOST={"decision":1.12,"evidence":1.08,"document":1.0,"meeting":.95,"task":.9}

def keyword_search(db,query,limit=30):
    weights=Counter()
    for x in query.topics: weights[x]+=3
    for x in query.facts: weights[x]+=3.5
    for x in query.entities: weights[x]+=3.5
    for x in TOKEN.findall(query.text): weights[x]+=1
    out=[]
    for i in db.scalars(select(KnowledgeItem).where(
        KnowledgeItem.workspace_id==query.workspace_id,
        or_(KnowledgeItem.project_id==query.project_id, KnowledgeItem.project_id.is_(None)),
    )).all():
        title=(i.title or "").lower(); content=(i.content or "").lower(); score=0; matched=[]
        for term,weight in weights.items():
            t=term.lower(); th=title.count(t); ch=content.count(t)
            if th or ch:
                matched.append(term); score+=th*2.2*weight+min(ch,3)*weight
        if score>0:
            out.append(RetrievalCandidate(i.id,i.object_type,i.source_id,i.source_type,i.title,i.content,keyword_score=score*BOOST.get(i.object_type,1),matched_terms=matched[:12]))
    out.sort(key=lambda x:(x.keyword_score,x.item_id),reverse=True)
    peak=out[0].keyword_score if out else 1
    for rank,x in enumerate(out,1): x.keyword_rank=rank; x.keyword_score/=peak
    return out[:limit]

