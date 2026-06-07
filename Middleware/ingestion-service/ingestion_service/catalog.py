"""Read access to the anime catalog (browse list + detail)."""

from __future__ import annotations

from anime_shared.db import session_scope
from anime_shared.exceptions import NotFoundError
from anime_shared.models import AnimeCatalog
from anime_shared.schemas import AnimeDetail, CatalogItem, CatalogPage
from sqlalchemy import func, select


def get_catalog_page(limit: int = 50, offset: int = 0) -> CatalogPage:
    limit = max(1, min(limit, 200))
    offset = max(0, offset)
    with session_scope() as session:
        total = session.scalar(select(func.count()).select_from(AnimeCatalog)) or 0
        rows = session.scalars(
            select(AnimeCatalog).order_by(AnimeCatalog.id).limit(limit).offset(offset)
        ).all()
        items = [
            CatalogItem(
                id=row.id,
                title=row.title,
                score=row.score,
                genres=row.genres,
                year=row.year,
                studio=row.studio,
                status=row.status,
            )
            for row in rows
        ]
    return CatalogPage(items=items, total=int(total), limit=limit, offset=offset)


def get_anime(anime_id: int) -> AnimeDetail:
    with session_scope() as session:
        row = session.get(AnimeCatalog, anime_id)
        if row is None:
            raise NotFoundError(f"Anime not found: {anime_id}")
        return AnimeDetail(
            id=row.id,
            title=row.title,
            synopsis=row.synopsis,
            genres=row.genres,
            score=row.score,
            year=row.year,
            episodes=row.episodes,
            studio=row.studio,
            status=row.status,
        )
