from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.audio_ws import router as audio_router
from app.api.health import router as health_router
from app.api.routes import router
from app.api.retrieval import router as retrieval_router
from app.api.retrieval_admin import router as retrieval_admin_router
from app.core.config import settings
from app.db.session import Base, engine
from app.observability.logging_config import configure_logging
from app.observability.middleware import RequestObservabilityMiddleware

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
app.include_router(retrieval_router)
app.include_router(retrieval_admin_router)
app.include_router(audio_router)
app.include_router(health_router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
