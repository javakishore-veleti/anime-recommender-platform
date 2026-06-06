"""Read access to the anime catalog (for the Admin UI)."""

from __future__ import annotations

from sqlalchemy import func, select

from anime_shared.db import session_scope
from anime_shared.models import AnimeCatalog
from anime_shared.schemas import CatalogItem, CatalogPage


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
                mal_id=row.mal_id,
                name=row.name,
                score=row.score,
                genres=row.genres,
                synopsis=row.synopsis,
            )
            for row in rows
        ]
    return CatalogPage(items=items, total=int(total), limit=limit, offset=offset)
