"""Менеджер базы данных SQLAlchemy для каталогов землетрясений."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import (
    Column, DateTime, Float, Integer, String, Text,
    create_engine, select,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger(__name__)

DEFAULT_DB = Path(__file__).parents[2] / "data" / "processed" / "seismic.db"


class Base(DeclarativeBase):
    """Базовый класс ORM моделей."""
    pass


class EventModel(Base):
    """Таблица событий в унифицированном формате."""
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, index=True)
    year = Column(Integer, index=True)
    year_error = Column(Integer)
    month = Column(Integer)
    day = Column(Integer)
    lat = Column(Float, index=True)
    lon = Column(Float, index=True)
    magnitude = Column(Float, index=True)
    magnitude_error = Column(Float)
    depth_km = Column(Float)
    region = Column(String(256))
    fe_region = Column(Integer, index=True)
    source_type = Column(String(32))
    reference = Column(String(128))
    quality_score = Column(Float)
    completeness_weight = Column(Float)


class SourceModel(Base):
    """Таблица источников данных."""
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128))
    version = Column(String(64))
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    record_count = Column(Integer)
    notes = Column(Text)


class FERegionModel(Base):
    """Таблица регионов Flinn-Engdahl."""
    __tablename__ = "fe_regions"

    id = Column(Integer, primary_key=True)
    number = Column(Integer, unique=True)
    name = Column(String(256))
    center_lat = Column(Float)
    center_lon = Column(Float)


class DBManager:
    """Менеджер SQLite-базы данных для сейсмических каталогов.

    Пример::

        db = DBManager()
        db.init_db()
        db.insert_events(df)
        result = db.query_events(min_mag=7.0, start_year=1990, end_year=2020)
    """

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._engine = create_engine(f"sqlite:///{self.db_path}", echo=False)
        self._Session = sessionmaker(bind=self._engine)

    def close(self) -> None:
        """Disposes the SQLAlchemy engine and releases all connections."""
        self._engine.dispose()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def init_db(self) -> None:
        """Создаёт таблицы в базе данных, если они не существуют."""
        Base.metadata.create_all(self._engine)
        logger.info("База данных инициализирована: %s", self.db_path)

        # Заполняем таблицу регионов Flinn-Engdahl
        from .unifier import FE_REGIONS
        with self._Session() as session:
            existing = session.execute(select(FERegionModel)).scalars().all()
            if not existing:
                for num, name, lat, lon in FE_REGIONS:
                    session.add(FERegionModel(
                        number=num, name=name, center_lat=lat, center_lon=lon,
                    ))
                session.commit()
                logger.info("Загружено %d регионов Flinn-Engdahl", len(FE_REGIONS))

    def insert_events(
        self,
        df: pd.DataFrame,
        source_name: str = "unknown",
    ) -> int:
        """Вставляет события из DataFrame, игнорируя дубликаты по event_id.

        Args:
            df: DataFrame с событиями.
            source_name: название источника для журнала.

        Returns:
            Количество вставленных записей.
        """
        inserted = 0
        with self._Session() as session:
            for _, row in df.iterrows():
                ev = self._row_to_model(row)
                try:
                    session.merge(ev)
                    inserted += 1
                except Exception as exc:
                    logger.debug("Пропущено событие %s: %s", row.get("event_id"), exc)
                    session.rollback()

            session.commit()

        # Записываем источник
        with self._Session() as session:
            session.add(SourceModel(
                name=source_name,
                record_count=inserted,
                fetched_at=datetime.now(timezone.utc),
            ))
            session.commit()

        logger.info("Вставлено %d событий из источника '%s'", inserted, source_name)
        return inserted

    def query_events(
        self,
        min_mag: float = 6.5,
        start_year: int = 1900,
        end_year: int = 2026,
        region: int | None = None,
    ) -> pd.DataFrame:
        """Извлекает события из базы данных по критериям.

        Args:
            min_mag: минимальная магнитуда.
            start_year: начальный год.
            end_year: конечный год.
            region: номер региона Flinn-Engdahl (None = все регионы).

        Returns:
            DataFrame с событиями.
        """
        stmt = select(EventModel).where(
            EventModel.magnitude >= min_mag,
            EventModel.year >= start_year,
            EventModel.year <= end_year,
        )
        if region is not None:
            stmt = stmt.where(EventModel.fe_region == region)

        with self._Session() as session:
            rows = session.execute(stmt).scalars().all()

        records = [self._model_to_dict(r) for r in rows]
        return pd.DataFrame(records)

    @staticmethod
    def _row_to_model(row: Any) -> EventModel:
        """Конвертирует строку DataFrame в ORM-модель."""
        def safe_float(val: Any) -> float | None:
            try:
                return float(val) if pd.notna(val) else None
            except (TypeError, ValueError):
                return None

        def safe_int(val: Any) -> int | None:
            try:
                return int(val) if pd.notna(val) else None
            except (TypeError, ValueError):
                return None

        return EventModel(
            event_id=str(row.get("event_id", "")),
            year=safe_int(row.get("year")),
            year_error=safe_int(row.get("year_error")),
            month=safe_int(row.get("month")),
            day=safe_int(row.get("day")),
            lat=safe_float(row.get("lat")),
            lon=safe_float(row.get("lon")),
            magnitude=safe_float(row.get("magnitude")),
            magnitude_error=safe_float(row.get("magnitude_error")),
            depth_km=safe_float(row.get("depth_km")),
            region=str(row.get("region", "")),
            fe_region=safe_int(row.get("fe_region")),
            source_type=str(row.get("source_type", "")),
            reference=str(row.get("reference", "")),
            quality_score=safe_float(row.get("quality_score")),
            completeness_weight=safe_float(row.get("completeness_weight")),
        )

    @staticmethod
    def _model_to_dict(model: EventModel) -> dict[str, Any]:
        """Конвертирует ORM-модель в словарь."""
        return {
            "event_id": model.event_id,
            "year": model.year,
            "year_error": model.year_error,
            "month": model.month,
            "day": model.day,
            "lat": model.lat,
            "lon": model.lon,
            "magnitude": model.magnitude,
            "magnitude_error": model.magnitude_error,
            "depth_km": model.depth_km,
            "region": model.region,
            "fe_region": model.fe_region,
            "source_type": model.source_type,
            "reference": model.reference,
            "quality_score": model.quality_score,
            "completeness_weight": model.completeness_weight,
        }
