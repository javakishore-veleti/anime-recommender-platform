"""FastAPI application factory shared across services.

Centralizes the boilerplate every service needs: structured logging, CORS for
the Angular portals, Prometheus metrics, OTel tracing, a ``/health`` endpoint,
and a uniform handler that maps :class:`AnimeRecommenderError` to HTTP responses.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from anime_shared.config import get_settings
from anime_shared.exceptions import AnimeRecommenderError
from anime_shared.logging import get_logger, setup_logging
from anime_shared.observability import setup_observability
from anime_shared.schemas import HealthResponse

# Angular dev servers (customer-portal :4200, admin-ui :4300).
DEFAULT_CORS_ORIGINS = [
    "http://localhost:4200",
    "http://localhost:4300",
]


def create_app(
    service_name: str,
    *,
    title: str | None = None,
    lifespan: Callable | None = None,
    cors_origins: list[str] | None = None,
) -> FastAPI:
    """Build a FastAPI app with the platform's shared cross-cutting concerns."""
    setup_logging(service_name)
    log = get_logger(service_name)

    app = FastAPI(title=title or service_name, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins or DEFAULT_CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AnimeRecommenderError)
    async def _handle_app_error(_: Request, exc: AnimeRecommenderError) -> JSONResponse:
        log.error("%s: %s", type(exc).__name__, exc)
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health() -> HealthResponse:
        return HealthResponse(service=service_name)

    setup_observability(app, service_name, get_settings())
    log.info("%s initialized", service_name)
    return app
