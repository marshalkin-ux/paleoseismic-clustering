"""
Agent 1 — Data Curator: database.py
=====================================
SQLAlchemy ORM for the unified earthquake catalogue.
Provides:
  - Table definitions (Events, Sources, Clusters)
  - Import / export helpers
  - Query convenience functions
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from sqlalchemy import (Boolean, Column, DateTime, Float, Integer, String,
                         Text, create_engine, text)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger(__name__)


# ── ORM Base and models ───────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(32), unique=True, nullable=False, index=True)
    year = Column(Integer, nullable=True, index=True)
    year_error = Column(Float, nullable=True)
    month = Column(Integer, nullable=True)
    day = Column(Integer, nullable=True)
    lat = Column(Float, nullable=False, index=True)
    lon = Column(Float, nullable=False, index=True)
    depth_km = Column(Float, nullable=True)
    magnitude = Column(Float, nullable=False, index=True)
    magnitude_error = Column(Float, nullable=True)
    mag_type = Column(String(16), nullable=True)
    region = Column(Text, nullable=True)
    source = Column(String(32), nullable=False, index=True)
    source_id = Column(String(64), nullable=True)
    reference = Column(Text, nullable=True)
    completeness_flag = Column(Boolean, nullable=True, index=True)


class ClusterMembership(Base):
    """Links events to detected clusters."""
    __tablename__ = "cluster_memberships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cluster_id = Column(String(32), nullable=False, index=True)
    event_id = Column(String(32), nullable=False, index=True)
    role = Column(String(16), nullable=True)   # 'mainshock' / 'member'


class DetectedCluster(Base):
    """Summary record for each detected global series."""
    __tablename__ = "detected_clusters"

    cluster_id = Column(String(32), primary_key=True)
    n_events = Column(Integer)
    start_year = Column(Integer)
    end_year = Column(Integer)
    duration_years = Column(Float)
    max_magnitude = Column(Float)
    mean_tectonic_distance_km = Column(Float)
    cluster_score = Column(Float)
    p_value = Column(Float)
    significant = Column(Boolean)
    time_window_days = Column(Integer)
    description = Column(Text)


# ── Engine and session factory ────────────────────────────────────────────────

def make_engine(db_path: str | Path):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}", echo=False,
                           connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine


def make_session(engine) -> Session:
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


# ── Import helpers ────────────────────────────────────────────────────────────

def import_catalogue(df: pd.DataFrame, db_path: str | Path,
                     replace: bool = False) -> int:
    """
    Bulk-import the unified catalogue DataFrame into the SQLite database.
    Returns the number of rows inserted.
    """
    engine = make_engine(db_path)

    # Map unified columns → ORM column names (they are identical here)
    cols = [c.key for c in Event.__table__.columns if c.key != "id"]
    df_db = df[[c for c in cols if c in df.columns]].copy()

    if replace:
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM events"))
            conn.commit()

    inserted = 0
    with Session(engine) as session:
        for _, row in df_db.iterrows():
            existing = session.query(Event).filter_by(
                event_id=row.get("event_id")).first()
            if existing is None:
                ev = Event(**{k: _none_if_nan(v) for k, v in row.items()})
                session.add(ev)
                inserted += 1
        session.commit()

    logger.info("Imported %d new events into %s", inserted, db_path)
    return inserted


def _none_if_nan(v):
    try:
        import math
        if math.isnan(float(v)):
            return None
    except (TypeError, ValueError):
        pass
    return v


# ── Query helpers ─────────────────────────────────────────────────────────────

def load_catalogue(db_path: str | Path,
                   min_mag: float = 6.5,
                   start_year: int = -100_000,
                   end_year: int = 2024,
                   complete_only: bool = True) -> pd.DataFrame:
    """
    Return catalogue as a DataFrame filtered by magnitude, time, and
    optionally restricted to completeness-flagged events.
    """
    engine = make_engine(db_path)
    query = (
        "SELECT * FROM events "
        "WHERE magnitude >= :min_mag "
        "  AND year >= :start_year "
        "  AND year <= :end_year "
    )
    if complete_only:
        query += "  AND completeness_flag = 1 "
    query += "ORDER BY year, month, day"

    with engine.connect() as conn:
        df = pd.read_sql_query(
            text(query),
            conn,
            params={"min_mag": min_mag,
                    "start_year": start_year,
                    "end_year": end_year},
        )
    logger.info("Loaded %d events from %s", len(df), db_path)
    return df


def save_clusters(clusters: list[dict], db_path: str | Path) -> None:
    """Persist detected cluster summaries and memberships."""
    engine = make_engine(db_path)
    with Session(engine) as session:
        for c in clusters:
            cluster_id = c["cluster_id"]
            # Upsert cluster summary
            existing = session.query(DetectedCluster).filter_by(
                cluster_id=cluster_id).first()
            if existing is None:
                session.add(DetectedCluster(**{
                    k: v for k, v in c.items()
                    if k in DetectedCluster.__table__.columns.keys()
                }))
            # Insert memberships
            for ev_id in c.get("event_ids", []):
                m = ClusterMembership(
                    cluster_id=cluster_id,
                    event_id=ev_id,
                    role="member",
                )
                session.add(m)
        session.commit()
    logger.info("Saved %d clusters to %s", len(clusters), db_path)


def load_clusters(db_path: str | Path) -> pd.DataFrame:
    engine = make_engine(db_path)
    with engine.connect() as conn:
        return pd.read_sql_query(
            text("SELECT * FROM detected_clusters ORDER BY p_value"),
            conn,
        )
