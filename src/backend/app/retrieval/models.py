from dataclasses import dataclass, field

@dataclass(slots=True)
class RetrievalQuery:
    project_id: str
    text: str
    topics: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    entities: list[str] = field(default_factory=list)
    top_k: int = 8

@dataclass(slots=True)
class RetrievalCandidate:
    item_id: str
    object_type: str
    source_id: str
    source_type: str
    title: str
    content: str
    keyword_score: float = 0.0
    vector_score: float = 0.0
    hybrid_score: float = 0.0
    keyword_rank: int | None = None
    vector_rank: int | None = None
    matched_terms: list[str] = field(default_factory=list)
    def as_dict(self):
        return {
            "itemId": self.item_id,
            "objectType": self.object_type,
            "objectId": self.source_id or self.item_id,
            "sourceType": self.source_type,
            "title": self.title,
            "summary": self.content,
            "score": round(self.hybrid_score,6),
            "scores":{"keyword":round(self.keyword_score,6),"vector":round(self.vector_score,6)},
            "ranks":{"keyword":self.keyword_rank,"vector":self.vector_rank},
            "matchedTerms": self.matched_terms,
        }
