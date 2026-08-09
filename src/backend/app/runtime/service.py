from sqlalchemy.orm import Session
from app.intelligence.reminder_engine import ai_reminder_engine
from app.models.entities import Meeting
from app.runtime.models import RuntimeState
from app.runtime.store import runtime_state_store
class RuntimeStateService:
    async def refresh(self,db:Session,meeting:Meeting)->RuntimeState:
        result=await ai_reminder_engine.generate(db,meeting)
        context=result["context"]; retrieval=result["retrieval"]
        state=RuntimeState(
            meetingId=meeting.id,projectId=meeting.project_id,contextId=context["contextId"],
            objective=context.get("currentObjective",""),canonicalContext=context.get("cleanTranscriptWindow",""),
            topics=list(context.get("topics") or []),facts=list(context.get("facts") or []),constraints=list(context.get("constraints") or []),
            retrievalMode=retrieval.get("mode","keyword"),retrievalResults=list(retrieval.get("results") or []),
            rerankedEvidence=list(result.get("rerankedEvidence") or []),reminders=list(result.get("reminders") or []),
            diagnostics={"reminder":result.get("diagnostics") or {},"retrieval":retrieval.get("diagnostics") or {}},
        )
        return runtime_state_store.put(state)
    async def get_or_refresh(self,db:Session,meeting:Meeting)->RuntimeState:
        return runtime_state_store.get(meeting.id) or await self.refresh(db,meeting)
runtime_state_service=RuntimeStateService()
