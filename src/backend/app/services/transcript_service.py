from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import Meeting, MeetingTranscriptSegment


_WHITESPACE_PATTERN = re.compile(r"\s+")
_PUNCTUATION_PATTERN = re.compile(r"[，。！？；：、,.!?;:\s]+")


@dataclass(slots=True)
class TranscriptAppendResult:
    segment: MeetingTranscriptSegment
    created: bool
    replaced_segment_id: str | None = None


def normalize_transcript_text(text: str) -> str:
    """Normalize ASR output without changing its business meaning."""
    normalized = _WHITESPACE_PATTERN.sub(" ", text or "").strip()
    return normalized


def transcript_fingerprint(text: str) -> str:
    """Create a loose fingerprint used only for short-window duplicate detection."""
    return _PUNCTUATION_PATTERN.sub("", normalize_transcript_text(text)).lower()


def _get_last_segment(
    db: Session,
    meeting_id: str,
) -> MeetingTranscriptSegment | None:
    return db.scalar(
        select(MeetingTranscriptSegment)
        .where(MeetingTranscriptSegment.meeting_id == meeting_id)
        .order_by(MeetingTranscriptSegment.sequence.desc())
        .limit(1)
    )


def _rebuild_meeting_transcript(db: Session, meeting: Meeting) -> None:
    texts = list(
        db.scalars(
            select(MeetingTranscriptSegment.text)
            .where(
                MeetingTranscriptSegment.meeting_id == meeting.id,
                MeetingTranscriptSegment.is_final.is_(True),
            )
            .order_by(MeetingTranscriptSegment.sequence.asc())
        ).all()
    )
    meeting.transcript = "\n".join(text for text in texts if text).strip()


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
) -> TranscriptAppendResult:
    clean_text = normalize_transcript_text(text)
    if not clean_text:
        raise ValueError("转写文本不能为空")

    last_segment = _get_last_segment(db, meeting.id)
    clean_fingerprint = transcript_fingerprint(clean_text)

    if last_segment:
        last_fingerprint = transcript_fingerprint(last_segment.text)

        # Exact duplicate: acknowledge it but do not persist it twice.
        if clean_fingerprint and clean_fingerprint == last_fingerprint:
            return TranscriptAppendResult(segment=last_segment, created=False)

        # Browser SpeechRecognition occasionally emits A and then A+B as two final
        # segments. Replace the immediately preceding shorter segment.
        if (
            clean_fingerprint
            and last_fingerprint
            and clean_fingerprint.startswith(last_fingerprint)
            and len(clean_fingerprint) > len(last_fingerprint)
            and len(clean_fingerprint) - len(last_fingerprint) <= 80
        ):
            replaced_id = last_segment.id
            last_segment.text = clean_text
            last_segment.confidence = confidence
            last_segment.start_ms = (
                start_ms if start_ms is not None else last_segment.start_ms
            )
            last_segment.end_ms = end_ms if end_ms is not None else last_segment.end_ms
            last_segment.asr_provider = provider
            last_segment.speaker = speaker or last_segment.speaker
            _rebuild_meeting_transcript(db, meeting)
            db.commit()
            db.refresh(last_segment)
            return TranscriptAppendResult(
                segment=last_segment,
                created=False,
                replaced_segment_id=replaced_id,
            )

    last_sequence = db.scalar(
        select(func.max(MeetingTranscriptSegment.sequence)).where(
            MeetingTranscriptSegment.meeting_id == meeting.id
        )
    )
    segment = MeetingTranscriptSegment(
        workspace_id=meeting.workspace_id,
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
    db.add(segment)
    db.flush()
    _rebuild_meeting_transcript(db, meeting)
    db.commit()
    db.refresh(segment)
    return TranscriptAppendResult(segment=segment, created=True)


def list_segments(db: Session, meeting_id: str, workspace_id: str | None = None) -> list[MeetingTranscriptSegment]:
    return list(
        db.scalars(
            select(MeetingTranscriptSegment)
            .where(MeetingTranscriptSegment.meeting_id == meeting_id, *([MeetingTranscriptSegment.workspace_id == workspace_id] if workspace_id else []))
            .order_by(MeetingTranscriptSegment.sequence.asc())
        ).all()
    )
