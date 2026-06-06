"""Loader tests against the bundled seed dataset."""

from __future__ import annotations

from ingestion_service.loader import load_rows, resolve_seed_csv


def test_seed_csv_resolves_to_repo_data():
    path = resolve_seed_csv()
    assert path.name == "anime_with_synopsis.csv"
    assert path.exists()


def test_load_rows_builds_combined_info():
    rows = load_rows()
    assert len(rows) > 0
    sample = rows[0]
    assert sample.combined_info.startswith("Title: ")
    assert "Overview:" in sample.combined_info
    assert "Genres:" in sample.combined_info
    assert sample.metadata["name"] == sample.name
