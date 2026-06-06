"""Centralized, validated configuration via pydantic-settings.

Replaces the original ``config/config.py`` which read a couple of values with
bare ``os.getenv`` calls. All services import :func:`get_settings`, so config is
defined once, validated, and cached.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Platform-wide settings loaded from environment / ``.env``."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- LLM (Groq) ----
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_model_name: str = Field(default="llama-3.1-8b-instant", alias="GROQ_MODEL_NAME")

    # ---- Embeddings ----
    huggingfacehub_api_token: str = Field(default="", alias="HUGGINGFACEHUB_API_TOKEN")
    embedding_model_name: str = Field(default="all-MiniLM-L6-v2", alias="EMBEDDING_MODEL_NAME")

    # ---- Postgres ----
    database_url: str = Field(
        default="postgresql+psycopg://anime:anime@localhost:5432/anime",
        alias="DATABASE_URL",
    )

    # ---- Redis ----
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    # ---- Chroma ----
    chroma_persist_dir: str = Field(default="./.chroma_db", alias="CHROMA_PERSIST_DIR")

    # ---- Inter-service URLs ----
    vectorstore_service_url: str = Field(
        default="http://localhost:8001", alias="VECTORSTORE_SERVICE_URL"
    )
    ingestion_service_url: str = Field(
        default="http://localhost:8002", alias="INGESTION_SERVICE_URL"
    )
    recommender_service_url: str = Field(
        default="http://localhost:8003", alias="RECOMMENDER_SERVICE_URL"
    )

    # ---- Recommendation behavior ----
    recommendation_cache_ttl_seconds: int = Field(
        default=86_400, alias="RECOMMENDATION_CACHE_TTL_SECONDS"
    )
    recommendation_top_k: int = Field(default=5, alias="RECOMMENDATION_TOP_K")

    # ---- Observability ----
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")  # "json" | "console"
    # Write JSON logs to <repo>/logs/<service>.jsonl so promtail can ship them to Loki.
    log_to_file: bool = Field(default=True, alias="LOG_TO_FILE")
    log_dir: str = Field(default="logs", alias="LOG_DIR")
    elasticsearch_url: str = Field(default="", alias="ELASTICSEARCH_URL")
    elasticsearch_log_index: str = Field(default="anime-logs", alias="ELASTICSEARCH_LOG_INDEX")
    otel_exporter_otlp_endpoint: str = Field(
        default="", alias="OTEL_EXPORTER_OTLP_ENDPOINT"
    )
    otel_traces_enabled: bool = Field(default=False, alias="OTEL_TRACES_ENABLED")

    # ---- Dataset (used by ingestion) ----
    seed_csv_path: str = Field(default="data/anime_with_synopsis.csv", alias="SEED_CSV_PATH")


@lru_cache
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
