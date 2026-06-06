"""recommender-service FastAPI entrypoint."""

from __future__ import annotations

from anime_shared.app_factory import create_app

from recommender_service.routers import router

app = create_app("recommender-service", title="Anime Recommender Service")
app.include_router(router)
