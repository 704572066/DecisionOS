from sqlalchemy import select

from app.meetings.summary_context import build_summary_context
from app.meetings.summary_extractor import meeting_summary_extractor
from app.meetings.summary_governance import summary_governance
from app.meetings.summary_models import MeetingSummaryResult
from app.models.entities import Meeting, MeetingFinalSnapshot, MeetingSummary


class MeetingSummaryService:
    def get(self, db, meeting: Meeting) -> MeetingSummary | None:
        return db.scalar(select(MeetingSummary).where(MeetingSummary.workspace_id == meeting.workspace_id, MeetingSummary.meeting_id == meeting.id))

    async def generate(self, db, meeting: Meeting) -> MeetingSummary:
        existing = self.get(db, meeting)
        if existing: return existing
        snapshot = db.scalar(select(MeetingFinalSnapshot).where(MeetingFinalSnapshot.workspace_id == meeting.workspace_id, MeetingFinalSnapshot.meeting_id == meeting.id))
        if not snapshot: raise ValueError("Final snapshot is required")
        context = build_summary_context(meeting.id, snapshot.payload)
        candidate, mode = await meeting_summary_extractor.extract(context)
        result = summary_governance.validate(context, candidate, extraction_mode=mode)
        row = MeetingSummary(workspace_id=meeting.workspace_id, meeting_id=meeting.id, snapshot_id=snapshot.id, result=result.model_dump(mode="json"))
        db.add(row); db.commit(); db.refresh(row)
        return row

    @staticmethod
    def result(row: MeetingSummary) -> MeetingSummaryResult:
        return MeetingSummaryResult.model_validate(row.result)


meeting_summary_service = MeetingSummaryService()

