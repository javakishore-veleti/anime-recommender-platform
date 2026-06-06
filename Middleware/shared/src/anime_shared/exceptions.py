"""Typed exception hierarchy for the platform.

Replaces the original ``utils/custom_exception.py``. That version captured the
traceback via ``sys.exc_info()`` inside ``__init__`` (fragile and only correct
while handling a live exception). Here we use a clean exception hierarchy and
preserve the cause through normal ``raise ... from`` chaining.
"""

from __future__ import annotations


class AnimeRecommenderError(Exception):
    """Base class for all application errors raised by the platform."""

    #: HTTP status code services should map this error to.
    status_code: int = 500

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        self.message = message
        self.cause = cause
        super().__init__(message)

    def __str__(self) -> str:  # pragma: no cover - trivial
        if self.cause is not None:
            return f"{self.message} (caused by {type(self.cause).__name__}: {self.cause})"
        return self.message


class ConfigurationError(AnimeRecommenderError):
    """Raised when configuration is missing or invalid (e.g. no GROQ_API_KEY)."""

    status_code = 500


class NotFoundError(AnimeRecommenderError):
    """Raised when a requested resource does not exist."""

    status_code = 404


class DownstreamServiceError(AnimeRecommenderError):
    """Raised when a downstream service (vectorstore, Groq, DB, Redis) fails."""

    status_code = 502
