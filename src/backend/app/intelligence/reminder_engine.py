from __future__ import annotations

import logging
import time

from sqlalchemy.orm import Session

from app.context.service import build_meeting_context
from app.core.config import settings
from app.intelligence.llm import llm_provider
from app.intelligence.models import AIReminder, ReminderSource
from app.intelligence.prompt_builder import build_prompt
from app.intelligence.reranker import rerank_context
from app.models.entities import Meeting
from app.retrieval.query_builder import build_retrieval_query
from app.retrieval.service import hybrid_retriever

logger = logging.getLogger("decisionos.intelligence.reminder_engine")


class AIReminderEngine:
    async def generate(
        self,
        db: Session,
        meeting: Meeting,
        *,
        retrieval_top_k: int | None = None,
        evidence_top_k: int | None = None,
    ) -> dict:
        started = time.perf_counter()
        retrieval_top_k = retrieval_top_k or int(
            getattr(settings, "reminder_retrieval_top_k", 8)
        )
        evidence_top_k = evidence_top_k or int(
            getattr(settings, "reminder_evidence_top_k", 5)
        )

        context_started = time.perf_counter()
        context = build_meeting_context(db, meeting)
        context_ms = (time.perf_counter() - context_started) * 1000

        retrieval_started = time.perf_counter()
        retrieval = await hybrid_retriever.search(
            db,
            build_retrieval_query(context, top_k=retrieval_top_k),
        )
        retrieval_ms = (time.perf_counter() - retrieval_started) * 1000

        rerank_started = time.perf_counter()
        evidence = rerank_context(
            context,
            retrieval["results"],
            top_k=evidence_top_k,
        )
        rerank_ms = (time.perf_counter() - rerank_started) * 1000

        llm_ms = 0.0
        llm_error = None
        generation_mode = "evidence-fallback"

        if evidence and llm_provider.enabled:
            try:
                system_prompt, user_prompt = build_prompt(context, evidence)
                llm_started = time.perf_counter()
                envelope = await llm_provider.generate_reminders(
                    system_prompt,
                    user_prompt,
                )
                llm_ms = (time.perf_counter() - llm_started) * 1000
                reminders = self._validate_sources(
                    envelope.reminders,
                    evidence,
                )[:3]
                generation_mode = "llm"
            except Exception as exc:
                llm_error = str(exc)
                logger.exception("AI reminder generation failed; using evidence fallback")
                reminders = self._fallback(context, evidence)
        else:
            reminders = self._fallback(context, evidence)

        total_ms = (time.perf_counter() - started) * 1000
        return {
            "meetingId": meeting.id,
            "context": context.model_dump(mode="json"),
            "topics": context.topics,
            "retrieval": retrieval,
            "rerankedEvidence": [
                {
                    **row.item,
                    "rerankScore": round(row.final_score, 6),
                    "contextScore": round(row.context_score, 6),
                    "rerankReasons": row.reasons,
                }
                for row in evidence
            ],
            "reminders": [reminder.websocket_dict() for reminder in reminders],
            "diagnostics": {
                "generationMode": generation_mode,
                "llmConfigured": llm_provider.enabled,
                "llmError": llm_error,
                "contextMs": round(context_ms, 2),
                "retrievalMs": round(retrieval_ms, 2),
                "rerankMs": round(rerank_ms, 2),
                "llmMs": round(llm_ms, 2),
                "totalMs": round(total_ms, 2),
            },
        }

    def _validate_sources(self, reminders, evidence):
        allowed = {}
        for row in evidence:
            item = row.item
            key = str(item.get("objectId") or item.get("itemId"))
            allowed[key] = {
                "type": item.get("sourceType") or item.get("objectType") or "knowledge",
                "id": key,
                "title": item.get("title") or "",
                "score": row.final_score,
            }

        validated = []
        for reminder in reminders:
            sources = []
            for source in reminder.sources:
                matched = allowed.get(source.id)
                if matched:
                    sources.append(ReminderSource(**matched))
            if not sources:
                continue
            reminder.sources = sources[:3]
            reminder.confidence = min(
                reminder.confidence,
                max(source.score for source in reminder.sources),
            )
            validated.append(reminder)
        return validated

    def _fallback(self, context, evidence):
        if not evidence:
            return []

        reminders = []
        for row in evidence[:3]:
            item = row.item
            source = ReminderSource(
                type=item.get("sourceType") or item.get("objectType") or "knowledge",
                id=str(item.get("objectId") or item.get("itemId")),
                title=item.get("title") or "",
                score=row.final_score,
            )
            text = f"{item.get('title','')} {item.get('summary','')}"
            reminder_type = "history"
            suggestion = ""
            reason = "该企业历史知识与当前会议上下文高度相关。"

            if any(term in text for term in ("风险", "逾期", "坏账", "不得", "必须", "担保")):
                reminder_type = "risk"
                suggestion = "建议在继续谈判前确认该约束是否适用于当前交易。"
                reason = "历史规则或风险信息与当前条件存在直接关联。"
            elif item.get("objectType") == "decision":
                reminder_type = "history"
                suggestion = "建议参考历史决策边界，但由当前负责人确认最终方案。"

            reminders.append(
                AIReminder(
                    type=reminder_type,
                    title=item.get("title") or "相关历史信息",
                    summary=item.get("summary") or "",
                    suggestion=suggestion,
                    reason=reason,
                    sources=[source],
                    confidence=max(0.3, min(0.95, row.final_score)),
                )
            )
        return reminders


ai_reminder_engine = AIReminderEngine()
