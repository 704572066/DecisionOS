from pydantic import BaseModel, Field

class CandidateEvidence(BaseModel):
    type: str
    id: str
    title: str = ""
    summary: str = ""
    score: float = Field(default=0.0, ge=0.0, le=1.0)

class DecisionCandidate(BaseModel):
    candidateId: str
    projectId: str
    meetingId: str
    contextId: str
    title: str
    summary: str
    statement: str
    reasons: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    evidence: list[CandidateEvidence] = Field(default_factory=list)
    suggestedTasks: list[str] = Field(default_factory=list)
    status: str = "draft"

class CandidateFromReminderRequest(BaseModel):
    reminder: dict

class ConfirmDecisionRequest(BaseModel):
    candidate: DecisionCandidate
    title: str | None = None
    statement: str | None = None
    taskTitle: str | None = None
    taskObjective: str | None = None
    taskOwner: str = ""
