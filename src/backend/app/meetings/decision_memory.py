import hashlib
import re
from datetime import datetime

from sqlalchemy import delete, select

from app.models.entities import DecisionMemory, KnowledgeItem, Meeting, MeetingSummary


REPLACEMENT = re.compile(r"(替代|取代|更新为|调整为|改为)")


def decision_attributes(text: str) -> dict:
    result = {}
    discount = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    payment = re.search(r"(\d+)\s*天", text)
    if discount: result["discountPercent"] = float(discount.group(1))
    if payment: result["paymentTermDays"] = int(payment.group(1))
    return result


class DecisionMemoryService:
    def sync(self, db, meeting: Meeting, summary: MeetingSummary) -> list[DecisionMemory]:
        result = summary.result or {}
        evidence_by_id = {row.get("sourceId"): row for row in result.get("evidence", [])}
        output = []
        for index, decision in enumerate(result.get("decisions", [])):
            text = str(decision.get("text") or "").strip()
            source_ids = [str(x) for x in decision.get("sourceIds", []) if x]
            grounded = [evidence_by_id[x] for x in source_ids if x in evidence_by_id]
            if not text or not source_ids or len(grounded) != len(source_ids):
                continue
            if any(row.get("sourceType") not in {"transcript", "event", "semantic"} for row in grounded):
                continue
            source_decision_id = "summary-decision-" + hashlib.sha256(f"{summary.id}:{index}:{text}".encode()).hexdigest()[:24]
            existing = db.scalar(select(DecisionMemory).where(DecisionMemory.source_decision_id == source_decision_id))
            if existing:
                output.append(existing); continue
            attrs = decision_attributes(text)
            subject = ",".join(sorted(attrs)) or "general"
            previous = None
            if attrs and REPLACEMENT.search(text):
                candidates = db.scalars(select(DecisionMemory).where(
                    DecisionMemory.workspace_id == meeting.workspace_id,
                    DecisionMemory.status == "active",
                    DecisionMemory.subject == subject,
                ).order_by(DecisionMemory.effective_at.desc())).all()
                previous = candidates[0] if candidates else None
            memory = DecisionMemory(
                workspace_id=meeting.workspace_id, source_meeting_id=meeting.id, source_summary_id=summary.id,
                source_decision_id=source_decision_id, supersedes_id=previous.id if previous else None,
                title=f"历史会议决策｜{meeting.title}", decision=text, subject=subject, status="active",
                confidence=1.0, source_ids=source_ids, evidence=grounded,
                attributes={"knowledgeRole": "historical_decision", "authority": "historical_reference", **attrs},
                effective_at=meeting.finalized_at or datetime.utcnow(),
            )
            db.add(memory); db.flush()
            item = KnowledgeItem(
                workspace_id=meeting.workspace_id, project_id=None, object_type="decision",
                title=memory.title,
                content=f"历史决策：{text}\n来源会议：{meeting.title}（{meeting.id}）\nDecision Memory：{memory.id}",
                source_type="decision_memory", source_id=memory.id,
            )
            db.add(item); db.flush(); memory.knowledge_item_id = item.id
            if previous:
                previous.status = "superseded"
                if previous.knowledge_item_id:
                    db.execute(delete(KnowledgeItem).where(KnowledgeItem.id == previous.knowledge_item_id, KnowledgeItem.workspace_id == meeting.workspace_id))
                    previous.knowledge_item_id = None
            output.append(memory)
        db.commit()
        return output

    def list(self, db, workspace_id: str, meeting_id: str | None = None):
        stmt = select(DecisionMemory).where(DecisionMemory.workspace_id == workspace_id)
        if meeting_id: stmt = stmt.where(DecisionMemory.source_meeting_id == meeting_id)
        return list(db.scalars(stmt.order_by(DecisionMemory.created_at.desc())).all())

    def revoke(self, db, workspace_id: str, memory_id: str) -> DecisionMemory | None:
        row = db.scalar(select(DecisionMemory).where(DecisionMemory.id == memory_id, DecisionMemory.workspace_id == workspace_id))
        if not row: return None
        row.status = "revoked"
        if row.knowledge_item_id:
            db.execute(delete(KnowledgeItem).where(KnowledgeItem.id == row.knowledge_item_id, KnowledgeItem.workspace_id == workspace_id))
            row.knowledge_item_id = None
        db.commit(); db.refresh(row)
        return row


decision_memory_service = DecisionMemoryService()

