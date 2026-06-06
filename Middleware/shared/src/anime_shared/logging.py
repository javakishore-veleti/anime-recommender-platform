"""Structured logging setup.

Replaces the original ``utils/logger.py``, which called ``logging.basicConfig``
at import time (global side effect, file-only, fixed format). Here each service
calls :func:`setup_logging` explicitly at startup; output is JSON (for promtail
-> Loki and for Elasticsearch ingestion) or human-friendly console.

Log shipping:
- **Loki**: promtail tails the JSON written to stdout (configured in DevOps).
- **Elasticsearch**: an optional handler indexes records directly when
  ``ELASTICSEARCH_URL`` is set.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

try:  # python-json-logger >= 3 moved the formatter to pythonjsonlogger.json
    from pythonjsonlogger.json import JsonFormatter
except ImportError:  # pragma: no cover - older python-json-logger
    from pythonjsonlogger.jsonlogger import JsonFormatter

from anime_shared.config import Settings, get_settings

_CONFIGURED = False


def _repo_root() -> Path:
    """Best-effort repo root (directory containing package.json), for the logs dir."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "package.json").exists():
            return parent
    return Path.cwd()


def _json_formatter(service_name: str) -> "JsonFormatter":
    return JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        rename_fields={"asctime": "timestamp", "levelname": "level"},
        static_fields={"service": service_name},
    )


class _ElasticsearchHandler(logging.Handler):
    """Best-effort log shipping to Elasticsearch.

    Failures to index never raise into the application path — observability must
    not take down a request.
    """

    def __init__(self, url: str, index: str, service: str) -> None:
        super().__init__()
        from elasticsearch import Elasticsearch  # local import: optional dependency path

        self._index = index
        self._service = service
        self._client = Elasticsearch(url, request_timeout=2, max_retries=1)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            doc: dict[str, Any] = {
                "service": self._service,
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            self._client.index(index=self._index, document=doc)
        except Exception:  # noqa: BLE001 - never let logging break the app
            pass


def setup_logging(service_name: str, settings: Settings | None = None) -> None:
    """Configure root logging for a service. Idempotent."""
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = settings or get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if settings.log_format == "json":
        handler.setFormatter(_json_formatter(service_name))
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
        )
    root.addHandler(handler)

    # JSON file handler so promtail can tail logs/<service>.jsonl and ship them to Loki.
    if settings.log_to_file:
        try:
            log_dir = Path(settings.log_dir)
            if not log_dir.is_absolute():
                log_dir = _repo_root() / settings.log_dir
            log_dir.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                log_dir / f"{service_name}.jsonl", maxBytes=10_000_000, backupCount=3
            )
            file_handler.setFormatter(_json_formatter(service_name))
            root.addHandler(file_handler)
        except OSError:  # pragma: no cover - never block startup on log file issues
            logging.getLogger(service_name).warning("Could not open log file handler")

    if settings.elasticsearch_url:
        try:
            root.addHandler(
                _ElasticsearchHandler(
                    settings.elasticsearch_url, settings.elasticsearch_log_index, service_name
                )
            )
        except Exception:  # noqa: BLE001 - ES is optional; degrade gracefully
            logging.getLogger(service_name).warning("Elasticsearch log handler unavailable")

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger. Logging must already be configured via :func:`setup_logging`."""
    return logging.getLogger(name)
