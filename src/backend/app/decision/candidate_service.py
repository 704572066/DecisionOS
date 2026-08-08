from uuid import uuid4
from sqlalchemy.orm import Session
from app.context.service import build_meeting_context
from app.decision.models import CandidateEvidence, DecisionCandidate
from app.models.entities import Meeting
from app.retrieval.query_builder import build_retrieval_query
from app.retrieval.service import hybrid_retriever
from app.intelligence.reranker import rerank_context

class DecisionCandidateService:
    async def from_reminder(self, db: Session, meeting: Meeting, reminder: dict) -> DecisionCandidate:
        context = build_meeting_context(db, meeting)
        retrieval = await hybrid_retriever.search(db, build_retrieval_query(context, top_k=8))
        ranked = rerank_context(context, retrieval["results"], top_k=5)
        requested = {str(x.get("id")) for x in (reminder.get("sources") or []) if x.get("id")}
        selected = [row for row in ranked if str(row.item.get("objectId") or row.item.get("itemId")) in requested]
        if not selected:
            selected = ranked[:3]
        evidence = [CandidateEvidence(
            type=row.item.get("sourceType") or row.item.get("objectType") or "knowledge",
            id=str(row.item.get("objectId") or row.item.get("itemId")),
            title=row.item.get("title") or "",
            summary=row.item.get("summary") or "",
            score=row.final_score,
        ) for row in selected[:5]]
        return DecisionCandidate(
            candidateId="candidate-" + uuid4().hex[:12],
            projectId=meeting.project_id,
            meetingId=meeting.id,
            contextId=context.contextId,
            title=self._title(reminder),
            summary=(reminder.get("summary") or "").strip(),
            statement=self._statement(reminder),
            reasons=self._reasons(reminder, evidence),
            risks=self._risks(reminder),
            evidence=evidence,
            suggestedTasks=self._tasks(context.topics, reminder),
        )
    @staticmethod
    def _title(reminder):
        value=(reminder.get("title") or "会议决策").strip()
        for prefix in ("风险：","提醒：","建议："):
            if value.startswith(prefix): value=value[len(prefix):].strip()
        return value[:220] or "会议决策"
    @staticmethod
    def _statement(reminder):
        suggestion=(reminder.get("suggestion") or "").strip()
        summary=(reminder.get("summary") or "").strip()
        return suggestion or ("基于当前会议与历史依据，需确认："+summary if summary else "基于当前会议提醒形成决策草案，待负责人确认。")
    @staticmethod
    def _reasons(reminder, evidence):
        out=[]
        reason=(reminder.get("reason") or "").strip()
        if reason: out.append(reason)
        for item in evidence:
            marker=f"参考：{item.title}"
            if item.title and marker not in out: out.append(marker)
        return out[:6]
    @staticmethod
    def _risks(reminder):
        summary=(reminder.get("summary") or "").strip()
        return [summary] if reminder.get("type")=="risk" and summary else []
    @staticmethod
    def _tasks(topics, reminder):
        out=[]
        if "利润" in topics or "价格" in topics: out.append("测算当前方案对毛利率和利润的影响")
        if "付款" in topics: out.append("确认可接受付款周期及必要的风险控制条件")
        if "合同" in topics: out.append("确认合同条款与审批要求")
        if "交付" in topics: out.append("确认交付时间与资源可行性")
        if (reminder.get("suggestion") or "").strip() and not out: out.append("跟进并确认该决策建议的执行方案")
        return out[:4]

decision_candidate_service=DecisionCandidateService()
