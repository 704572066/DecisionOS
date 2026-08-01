import re
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.entities import KnowledgeItem, Meeting

KEYWORDS = {
    "价格": ["价格", "降价", "折扣", "报价"],
    "付款": ["付款", "账期", "周期", "90天", "30天"],
    "利润": ["利润", "毛利", "利润率"],
    "风险": ["风险", "逾期", "违约"]
}

def analyze_meeting(db: Session, meeting: Meeting) -> dict:
    text = meeting.transcript or ""
    matched = {topic for topic, words in KEYWORDS.items() if any(word in text for word in words)}
    items = db.scalars(select(KnowledgeItem).where(KnowledgeItem.project_id == meeting.project_id)).all()
    scored = []
    for item in items:
        score = 0
        for topic, words in KEYWORDS.items():
            if topic in matched and any(word in item.content or word in item.title for word in words):
                score += 3
        for token in set(re.findall(r"[\u4e00-\u9fff]{2,}|\d+%|\d+天", text)):
            if token in item.content:
                score += 1
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    reminders = [{
        "title": item.title,
        "summary": item.content,
        "source": {"type": item.source_type, "id": item.source_id or item.id},
        "relevanceScore": min(1.0, score / 10)
    } for score, item in scored[:5]]
    if not reminders:
        reminders = [{
            "title": "暂未发现高相关历史信息",
            "summary": "当前内容已记录。继续输入更多业务细节后再次分析。",
            "source": {"type": "system", "id": "context-engine"},
            "relevanceScore": 0.1
        }]
    return {"meetingId": meeting.id, "topics": sorted(matched), "reminders": reminders}
