#!/usr/bin/env python
"""
Step 1 — Download and normalise all earthquake catalogue data.

Usage
-----
    python scripts/download_data.py [--force] [--config CONFIG]

Options
-------
--force     Re-download even if cached files exist.
--config    Path to config.yaml (default: config.yaml).
--min-mag   Minimum magnitude (default: 6.5).
--start     Start year for USGS/ISC download (default: 1900).
--end       End year (default: 2024).
--sources   Comma-separated list: usgs,noaa,isc (default: all).
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

PYTHON = sys.executable


def main():
    parser = argparse.ArgumentParser(description="Download earthquake catalogue data")
    parser.add_argument("--force", action="store_true",
                        help="Re-download cached files")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--min-mag", type=float, default=6.5)
    parser.add_argument("--start", type=int, default=1900)
    parser.add_argument("--end", type=int, default=2024)
    parser.add_argument("--sources", default="usgs,noaa",
                        help="Which sources to download: usgs,noaa,isc")
    args = parser.parse_args()

    with open(args.config) as fh:
        config = yaml.safe_load(fh)

    sources = [s.strip().lower() for s in args.sources.split(",")]

    logger.info("=" * 60)
    logger.info("Paleoseismic Clustering — Data Collection Pipeline")
    logger.info("Sources: %s | M≥%.1f | %d–%d", ", ".join(sources),
                args.min_mag, args.start, args.end)
    logger.info("=" * 60)

    dfs = []
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    # ── USGS ComCat ────────────────────────────────────────────────────────────
    if "usgs" in sources:
        logger.info("\n[USGS] Downloading ComCat (M≥%.1f, %d–%d) …",
                    args.min_mag, args.start, args.end)
        try:
            from src.curator.usgs_fetcher import USGSFetcher
            fetcher = USGSFetcher()
            fetcher.fetch(min_magnitude=args.min_mag,
                         start_year=args.start, end_year=args.end)
            df_usgs = fetcher.to_dataframe()
            logger.info("USGS: %d events downloaded", len(df_usgs))
            dfs.append(df_usgs)
        except Exception as exc:
            logger.error("USGS fetch failed: %s", exc)

    # ── NOAA NGDC ──────────────────────────────────────────────────────────────
    if "noaa" in sources:
        logger.info("\n[NOAA] Downloading NGDC historical catalogue …")
        try:
            from src.curator.noaa_fetcher import NOAAFetcher
            fetcher = NOAAFetcher()
            fetcher.fetch(min_magnitude=args.min_mag)
            df_noaa = fetcher.to_dataframe()
            logger.info("NOAA: %d events downloaded", len(df_noaa))
            dfs.append(df_noaa)
        except Exception as exc:
            logger.error("NOAA fetch failed: %s", exc)

    # ── ISC Bulletin ───────────────────────────────────────────────────────────
    if "isc" in sources:
        logger.info("\n[ISC] Downloading Bulletin (M≥%.1f, %d–%d) …",
                    args.min_mag, args.start, args.end)
        try:
            from src.curator.isc_fetcher import ISCFetcher
            fetcher = ISCFetcher()
            fetcher.fetch(min_magnitude=args.min_mag,
                         start_year=args.start, end_year=args.end)
            df_isc = fetcher.to_dataframe()
            logger.info("ISC: %d events downloaded", len(df_isc))
            dfs.append(df_isc)
        except Exception as exc:
            logger.error("ISC fetch failed: %s", exc)

    if not dfs:
        logger.error("No data downloaded — check network connectivity")
        sys.exit(1)

    # ── Unify and deduplicate ──────────────────────────────────────────────────
    logger.info("\n[UNIFY] Merging %d catalogues …", len(dfs))
    from src.curator.unifier import CatalogUnifier
    unifier = CatalogUnifier()
    unified = unifier.merge(dfs)
    logger.info("Unified catalogue: %d events after deduplication", len(unified))

    # Save unified catalogue
    csv_path = processed_dir / "unified_catalogue.csv"
    unified.to_csv(csv_path, index=False)
    logger.info("CSV saved: %s", csv_path)

    try:
        parquet_path = processed_dir / "unified_catalogue.parquet"
        unified.to_parquet(parquet_path, index=False)
        logger.info("Parquet saved: %s", parquet_path)
    except Exception as exc:
        logger.warning("Parquet save failed (%s); CSV is still available", exc)

    # ── Load into SQLite ───────────────────────────────────────────────────────
    logger.info("\n[DB] Importing into SQLite …")
    db_path = Path(config["data"]["paths"]["db"])
    db_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from src.curator.db_manager import DBManager
        db = DBManager(db_path=db_path)
        db.init_db()

        # Add completeness weight column if missing
        if "completeness_weight" not in unified.columns:
            unified["completeness_weight"] = 1.0
        if "fe_region" not in unified.columns:
            unified["fe_region"] = 0

        n = db.insert_events(unified)
        logger.info("DB: %d events inserted → %s", n, db_path)
    except Exception as exc:
        logger.error("DB import failed: %s", exc)

    # ── Summary ────────────────────────────────────────────────────────────────
    logger.info("\n%s", "=" * 60)
    logger.info("DATA COLLECTION COMPLETE")
    logger.info("  Total events:    %d", len(unified))
    logger.info("  Year range:      %s – %s",
                unified["year"].min(), unified["year"].max())
    if "source_type" in unified.columns:
        logger.info("  Sources:         %s",
                    ", ".join(unified["source_type"].unique()))
    logger.info("  Output:          %s", processed_dir)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
