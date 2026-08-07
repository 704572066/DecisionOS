TYPE={"decision":.04,"evidence":.03,"document":.015}
def fuse_candidates(keyword,vector,top_k):
    merged={x.item_id:x for x in keyword}
    for v in vector:
        x=merged.get(v.item_id)
        if x: x.vector_score=v.vector_score; x.vector_rank=v.vector_rank
        else: merged[v.item_id]=v
    for x in merged.values():
        kr=1/(60+x.keyword_rank) if x.keyword_rank else 0
        vr=1/(60+x.vector_rank) if x.vector_rank else 0
        score=.45*(.55*x.keyword_score+.45*kr*60)+.55*(.70*x.vector_score+.30*vr*60)+TYPE.get(x.object_type,0)
        x.hybrid_score=max(0,min(1,score))
    return sorted(merged.values(),key=lambda x:(x.hybrid_score,x.vector_score,x.keyword_score),reverse=True)[:top_k]
