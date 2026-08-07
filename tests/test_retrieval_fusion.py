from app.retrieval.fusion import fuse_candidates
from app.retrieval.models import RetrievalCandidate

def make(item_id, keyword=0, vector=0, kr=None, vr=None):
    return RetrievalCandidate(
        item_id=item_id,
        object_type="evidence",
        source_id=item_id,
        source_type="evidence",
        title=item_id,
        content=item_id,
        keyword_score=keyword,
        vector_score=vector,
        keyword_rank=kr,
        vector_rank=vr,
    )

def test_item_supported_by_both_channels_ranks_first():
    keyword = [make("both", keyword=1, kr=1), make("keyword", keyword=.9, kr=2)]
    vector = [make("both", vector=.9, vr=1), make("vector", vector=.95, vr=2)]
    result = fuse_candidates(keyword, vector, 3)
    assert result[0].item_id == "both"
