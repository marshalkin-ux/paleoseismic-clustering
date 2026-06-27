"""Юнит-тесты модуля куратора данных."""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.curator.unifier import CatalogUnifier
from src.curator.db_manager import DBManager


def _make_test_df(n: int = 5, source: str = "USGS ComCat") -> pd.DataFrame:
    """Создаёт тестовый DataFrame в унифицированном формате."""
    import numpy as np
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "event_id": [f"{source[:3]}_{i}" for i in range(n)],
        "year":  [2000 + i for i in range(n)],
        "year_error": [0] * n,
        "month": [1] * n,
        "day":   [1] * n,
        "lat":   rng.uniform(-60, 60, size=n),
        "lon":   rng.uniform(-180, 180, size=n),
        "magnitude": rng.uniform(6.5, 8.0, size=n),
        "magnitude_error": [0.1] * n,
        "depth_km": rng.uniform(5, 100, size=n),
        "region": [f"Region {i}" for i in range(n)],
        "source_type": ["instrumental"] * n,
        "reference": [source] * n,
        "quality_score": [0.9] * n,
    })


class TestCatalogUnifier:
    """Тесты объединения каталогов."""

    def test_merge_single_catalog(self) -> None:
        """Объединение одного каталога должно возвращать тот же DataFrame."""
        df = _make_test_df(n=5)
        unifier = CatalogUnifier()
        result = unifier.merge([df])
        assert len(result) == 5

    def test_merge_no_duplicates(self) -> None:
        """После объединения не должно быть дубликатов event_id."""
        df1 = _make_test_df(n=5, source="USGS ComCat")
        df2 = _make_test_df(n=5, source="ISC Bulletin")
        unifier = CatalogUnifier()
        result = unifier.merge([df1, df2])
        # Все event_id уникальны
        assert result["event_id"].nunique() == len(result)

    def test_spatial_deduplication(self) -> None:
        """События в радиусе 50 км и 30 дней должны быть дедуплицированы."""
        import numpy as np
        # Два почти одинаковых события в одном месте
        df1 = pd.DataFrame({
            "event_id": ["ev_isc_1"],
            "year": [2000], "year_error": [0],
            "month": [1], "day": [1],
            "lat": [35.0], "lon": [135.0],
            "magnitude": [7.0], "magnitude_error": [None],
            "depth_km": [30.0], "region": ["Japan"],
            "source_type": ["instrumental"],
            "reference": ["ISC Bulletin"],
            "quality_score": [0.9],
        })
        df2 = pd.DataFrame({
            "event_id": ["ev_usgs_1"],
            "year": [2000], "year_error": [0],
            "month": [1], "day": [2],   # на 1 день позже — дубль
            "lat": [35.001], "lon": [135.001],  # почти то же место
            "magnitude": [7.0], "magnitude_error": [None],
            "depth_km": [30.0], "region": ["Japan"],
            "source_type": ["instrumental"],
            "reference": ["USGS ComCat"],
            "quality_score": [0.9],
        })
        unifier = CatalogUnifier(spatial_threshold_km=50, time_threshold_days=30)
        result = unifier.merge([df1, df2])
        # Должно остаться одно событие (ISC имеет приоритет)
        assert len(result) == 1
        assert result.iloc[0]["event_id"] == "ev_isc_1"

    def test_assign_flinn_engdahl(self) -> None:
        """Всем событиям должен быть присвоен регион Flinn-Engdahl."""
        df = _make_test_df(n=10)
        unifier = CatalogUnifier()
        result = unifier.assign_flinn_engdahl(df)
        assert "fe_region" in result.columns
        assert result["fe_region"].notna().all()

    def test_fe_region_values_in_range(self) -> None:
        """Номера регионов Flinn-Engdahl должны быть в диапазоне 1–50."""
        df = _make_test_df(n=20)
        unifier = CatalogUnifier()
        result = unifier.assign_flinn_engdahl(df)
        assert (result["fe_region"] >= 1).all()
        assert (result["fe_region"] <= 50).all()

    def test_save_and_load_csv(self) -> None:
        """Сохранённый CSV должен содержать то же число строк."""
        df = _make_test_df(n=5)
        unifier = CatalogUnifier()
        merged = unifier.merge([df])

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test_catalog.csv"
            unifier.save(merged, path)
            assert path.exists()
            loaded = pd.read_csv(path)
            assert len(loaded) == len(merged)


class TestDBManager:
    """Тесты менеджера базы данных."""

    def test_init_db(self) -> None:
        """Инициализация БД не должна выдавать исключений."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = DBManager(db_path=db_path)
            db.init_db()
            assert db_path.exists()

    def test_insert_and_query_events(self) -> None:
        """После вставки событий их должно быть видно в запросе."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = DBManager(db_path=db_path)
            db.init_db()

            df = _make_test_df(n=5)
            df["fe_region"] = 1
            df["completeness_weight"] = 1.0

            inserted = db.insert_events(df, source_name="test")
            assert inserted == 5

            result = db.query_events(min_mag=6.0, start_year=1990, end_year=2030)
            assert len(result) == 5

    def test_query_filter_by_magnitude(self) -> None:
        """Фильтрация по магнитуде должна работать корректно."""
        import numpy as np
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = DBManager(db_path=db_path)
            db.init_db()

            df = pd.DataFrame({
                "event_id": ["e1", "e2", "e3"],
                "year": [2000, 2001, 2002],
                "year_error": [0, 0, 0],
                "month": [1, 1, 1],
                "day": [1, 1, 1],
                "lat": [35.0, 36.0, 37.0],
                "lon": [135.0, 136.0, 137.0],
                "magnitude": [6.5, 7.0, 8.0],
                "magnitude_error": [None, None, None],
                "depth_km": [30.0, 30.0, 30.0],
                "region": ["A", "B", "C"],
                "fe_region": [1, 1, 1],
                "source_type": ["instrumental"] * 3,
                "reference": ["USGS ComCat"] * 3,
                "quality_score": [0.9, 0.9, 0.9],
                "completeness_weight": [1.0, 1.0, 1.0],
            })

            db.insert_events(df)

            result = db.query_events(min_mag=7.0, start_year=1990, end_year=2030)
            assert len(result) == 2
            assert all(result["magnitude"] >= 7.0)
