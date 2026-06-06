"""Shared cross-cutting library for the anime recommender Middleware services.

Provides centralized configuration, structured logging, typed exceptions,
database models/session, Redis access, shared DTO schemas, and observability
(Prometheus metrics + OpenTelemetry tracing) wiring reused across services.
"""

from anime_shared.config import Settings, get_settings
from anime_shared.exceptions import (
    AnimeRecommenderError,
    ConfigurationError,
    DownstreamServiceError,
    NotFoundError,
)
from anime_shared.logging import get_logger, setup_logging

__all__ = [
    "Settings",
    "get_settings",
    "get_logger",
    "setup_logging",
    "AnimeRecommenderError",
    "ConfigurationError",
    "DownstreamServiceError",
    "NotFoundError",
]
