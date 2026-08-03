from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import Meeting, MeetingTranscriptSegment


def append_final_segment(
    db: Session,
    *,
    meeting: Meeting,
    text: str,
    provider: str,
    confidence: float | None = None,
    start_ms: int | None = None,
    end_ms: int | None = None,
    speaker: str = "",
) -> MeetingTranscriptSegment:
    clean_text = text.strip()
    if not clean_text:
        raise ValueError("转写文本不能为空")

    last_sequence = db.scalar(
        select(func.max(MeetingTranscriptSegment.sequence)).where(
            MeetingTranscriptSegment.meeting_id == meeting.id
        )
    )
    segment = MeetingTranscriptSegment(
        meeting_id=meeting.id,
        sequence=(last_sequence or 0) + 1,
        speaker=speaker,
        text=clean_text,
        is_final=True,
        start_ms=start_ms,
        end_ms=end_ms,
        confidence=confidence,
        asr_provider=provider,
    )
    meeting.transcript = (meeting.transcript + "\n" + clean_text).strip()
    db.add(segment)
    db.commit()
    db.refresh(segment)
    return segment


def list_segments(db: Session, meeting_id: str) -> list[MeetingTranscriptSegment]:
    return list(
        db.scalars(
            select(MeetingTranscriptSegment)
            .where(MeetingTranscriptSegment.meeting_id == meeting_id)
            .order_by(MeetingTranscriptSegment.sequence.asc())
        ).all()
    )
