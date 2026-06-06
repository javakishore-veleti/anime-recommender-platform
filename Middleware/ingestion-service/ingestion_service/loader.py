"""CSV loading + cleaning.

Ports the logic from the original ``src/data_loader.py`` (build a ``combined_info``
field from Title / Overview / Genres) but returns structured rows for both Postgres
and the vector store instead of writing an intermediate CSV. The dataset's original
``sypnopsis`` column spelling is preserved when reading.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from anime_shared.config import get_settings
from anime_shared.exceptions import ConfigurationError

REQUIRED_COLUMNS = {"Name", "Genres", "sypnopsis"}


@dataclass
class AnimeRow:
    name: str
    genres: str
    synopsis: str
    combined_info: str
    mal_id: int | None = None
    score: float | None = None
    metadata: dict[str, str] = field(default_factory=dict)


def _repo_root() -> Path:
    """Find the repo root by walking up to the directory containing package.json."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "package.json").exists():
            return parent
    return Path.cwd()


def resolve_seed_csv(source: str | None = None) -> Path:
    """Resolve the dataset path, accepting absolute or repo-root-relative paths."""
    settings = get_settings()
    raw = source or settings.seed_csv_path
    path = Path(raw)
    if not path.is_absolute():
        path = _repo_root() / raw
    return path


def load_rows(source: str | None = None) -> list[AnimeRow]:
    """Load and clean the dataset into structured rows."""
    csv_path = resolve_seed_csv(source)
    if not csv_path.exists():
        raise ConfigurationError(f"Dataset not found: {csv_path}")

    df = pd.read_csv(csv_path, encoding="utf-8", on_bad_lines="skip").dropna()

    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ConfigurationError(f"Missing columns in CSV: {sorted(missing)}")

    df["combined_info"] = (
        "Title: " + df["Name"]
        + " Overview: " + df["sypnopsis"]
        + " Genres: " + df["Genres"]
    )

    rows: list[AnimeRow] = []
    for _, r in df.iterrows():
        mal_id = int(r["MAL_ID"]) if "MAL_ID" in df.columns and not pd.isna(r["MAL_ID"]) else None
        score = float(r["Score"]) if "Score" in df.columns and not pd.isna(r["Score"]) else None
        rows.append(
            AnimeRow(
                name=str(r["Name"]),
                genres=str(r["Genres"]),
                synopsis=str(r["sypnopsis"]),
                combined_info=str(r["combined_info"]),
                mal_id=mal_id,
                score=score,
                metadata={"name": str(r["Name"]), "genres": str(r["Genres"])},
            )
        )
    return rows
