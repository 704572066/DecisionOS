from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.audio_ws import router as audio_router
from app.api.routes import router
from app.core.config import settings
from app.db.session import Base, engine

app = FastAPI(title="DecisionOS Demo API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
app.include_router(audio_router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "asrProvider": settings.asr_provider,
        "asrLanguage": settings.asr_language,
    }
