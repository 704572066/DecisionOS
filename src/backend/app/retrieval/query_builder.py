from app.retrieval.models import RetrievalQuery

def build_retrieval_query(context, top_k=8):
    facts=[x.normalizedValue or x.text for x in context.facts if (x.normalizedValue or x.text)]
    entities=[x.name for x in context.entities]
    parts=[context.cleanTranscriptWindow.strip()]
    if context.currentObjective: parts.append("业务目标："+context.currentObjective)
    if context.topics: parts.append("当前议题："+"、".join(context.topics))
    if facts: parts.append("关键事实："+"、".join(facts))
    if entities: parts.append("业务实体："+"、".join(entities))
    return RetrievalQuery(context.projectId,"\n".join(x for x in parts if x),list(context.topics),facts,entities,top_k)
