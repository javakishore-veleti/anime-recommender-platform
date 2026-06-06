"""vectorstore-service FastAPI entrypoint."""

from __future__ import annotations

from anime_shared.app_factory import create_app

from vectorstore_service.routers import router

app = create_app("vectorstore-service", title="Anime Vectorstore Service")
app.include_router(router)
