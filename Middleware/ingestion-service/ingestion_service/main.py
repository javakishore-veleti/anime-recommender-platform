"""ingestion-service FastAPI entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from anime_shared.app_factory import create_app
from anime_shared.db import create_all
from anime_shared.logging import get_logger
from fastapi import FastAPI

from ingestion_service.routers import router

log = get_logger("ingestion-service")


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create tables on startup for local dev (use migrations in production).
    try:
        create_all()
    except Exception:  # noqa: BLE001 - DB may not be up yet; endpoints will surface errors
        log.warning("Could not create tables at startup (is Postgres running?)")
    yield


app = create_app("ingestion-service", title="Anime Ingestion Service", lifespan=lifespan)
app.include_router(router)
