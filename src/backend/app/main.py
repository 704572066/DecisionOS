from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.audio_ws import router as audio_router
from app.api.health import router as health_router
from app.api.routes import router
from app.api.retrieval import router as retrieval_router
from app.api.retrieval_admin import router as retrieval_admin_router
from app.api.ai_reminder import router as ai_reminder_router
from app.api.decision_candidates import router as decision_candidate_router
from app.api.decision_board import router as decision_board_router
from app.api.dialogue import router as dialogue_router
from app.api.intervention_delivery import router as intervention_delivery_router
from app.api.auth import router as auth_router
from app.api.knowledge import router as knowledge_router
from app.api.meeting_history import router as meeting_history_router
from app.core.config import settings
from app.db.session import Base, engine
from app.observability.logging_config import configure_logging
from app.observability.middleware import RequestObservabilityMiddleware
from app.auth.bootstrap import bootstrap_legacy_owner

configure_logging()

app = FastAPI(title=settings.app_name, version="0.2.1")
app.add_middleware(RequestObservabilityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
app.include_router(ai_reminder_router)
app.include_router(decision_candidate_router)
app.include_router(retrieval_router)
app.include_router(retrieval_admin_router)
app.include_router(audio_router)
app.include_router(health_router)
app.include_router(decision_board_router)
app.include_router(dialogue_router)
app.include_router(intervention_delivery_router)
app.include_router(auth_router)
app.include_router(knowledge_router)
app.include_router(meeting_history_router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    bootstrap_legacy_owner()

