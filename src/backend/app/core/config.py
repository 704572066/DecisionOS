from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DecisionOS Demo API"
    app_environment: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://decisionos:decisionos@localhost:5432/decisionos"
    openai_base_url: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    cors_origins: str = "http://localhost:5173"

    asr_provider: str = "browser"
    asr_language: str = "zh-CN"
    deepgram_api_key: str = ""
    deepgram_model: str = "nova-3"
    deepgram_endpointing_ms: int = 300

    reminder_min_chars: int = 30
    reminder_cooldown_seconds: int = 3

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
