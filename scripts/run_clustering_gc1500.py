#!/usr/bin/env python
"""Run global-series detection with mean pairwise GC > 1500 km criterion.

Outputs:
    results/clustering_gc1500.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis.clustering import SeismicClusterAnalyzer, DEFAULT_MIN_MEAN_GC_KM
from src.analysis.etas_validation import assign_fe_regions

CATALOG = ROOT / "data" / "processed" / "unified_catalog_full.csv"
OUT = ROOT / "results" / "clustering_gc1500.json"


def _count_series(df: pd.DataFrame, time_window: float, min_events: int) -> dict:
    analyzer = SeismicClusterAnalyzer()
    series = analyzer.global_series(
        df,
        time_window_years=time_window,
        min_events=min_events,
        min_mean_gc_km=DEFAULT_MIN_MEAN_GC_KM,
    )
    rows = []
    for s in series:
        rows.append({
            "n_events": len(s),
            "mean_pairwise_gc_km": float(s["mean_pairwise_gc_km"].iloc[0]),
            "n_fe_regions": int(s["fe_region"].nunique()) if "fe_region" in s.columns else None,
            "year_start": int(s["year"].min()),
            "year_end": int(s["year"].max()),
        })
    return {
        "n_series": len(series),
        "time_window_years": time_window,
        "min_events": min_events,
        "min_mean_gc_km": DEFAULT_MIN_MEAN_GC_KM,
        "criterion": "mean_pairwise_gc_km > 1500 (all unordered pairs)",
        "fe_regions": "diagnostic only, not a gate",
        "series": rows,
    }


def main() -> None:
    df = pd.read_csv(CATALOG, low_memory=False)
    df = df[df["magnitude"] >= 6.5].dropna(subset=["lat", "lon"])
    df = assign_fe_regions(df)

    modern = df[df["year"] >= 1973].copy()
    full = df.copy()

    # Legacy FE gate for comparison (same windows)
    analyzer = SeismicClusterAnalyzer()
    legacy_modern = analyzer.global_series(
        modern, time_window_years=2.0, min_events=4, min_mean_gc_km=0.0, min_regions=3,
    )

    out = {
        "catalog_n_m65": len(full),
        "modern_n_m65": len(modern),
        "modern_gc1500": _count_series(modern, time_window=2.0, min_events=4),
        "full_gc1500_windows": {
            "modern_2yr": _count_series(modern, 2.0, 4),
            "early_5yr": _count_series(
                df[(df["year"] >= 1900) & (df["year"] < 1973)], 5.0, 3
            ),
            "historical_50yr": _count_series(df[df["year"] < 1900], 50.0, 3),
        },
        "legacy_fe_min3_modern_2yr_n_series": len(legacy_modern),
        "note": (
            "Primary gate: mean pairwise great-circle distance > 1500 km. "
            "4267 unique M>=6.5 events; 4418 CSV rows include ~151 NOAA M<6.5 "
            "retained for provenance, excluded from clustering."
        ),
    }
    out["n_series_total_three_epochs"] = sum(
        out["full_gc1500_windows"][k]["n_series"] for k in out["full_gc1500_windows"]
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Modern N_series (GC>1500 km): {out['modern_gc1500']['n_series']}")
    print(f"Legacy FE>=3 N_series (modern): {out['legacy_fe_min3_modern_2yr_n_series']}")
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
