from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DecisionOS Demo API"
    app_environment: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://decisionos:decisionos@localhost:5432/decisionos"
    openai_base_url: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    llm_timeout_seconds: float = 30.0
    llm_json_mode: bool = False
    reminder_temperature: float = 0.1
    reminder_enable_thinking: bool = False
    semantic_event_enabled: bool = True
    semantic_event_min_confidence: float = 0.72
    reminder_retrieval_top_k: int = 8
    reminder_evidence_top_k: int = 5
    cors_origins: str = "http://localhost:5173"
    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    embedding_send_dimensions: bool = False
    embedding_timeout_seconds: float = 20.0

    asr_provider: str = "browser"
    asr_language: str = "zh-CN"
    deepgram_api_key: str = ""
    deepgram_model: str = "nova-3"
    deepgram_endpointing_ms: int = 300

    reminder_min_chars: int = 30
    reminder_cooldown_seconds: int = 3

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
