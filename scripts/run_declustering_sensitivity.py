#!/usr/bin/env python
"""Declustering sensitivity for modern-window global-series detection.

Compares Gardner-Knopoff (baseline), Zaliapin-Ben-Zion, and no declustering
under fixed series gates: 2 yr window, mean GC > 1500 km, min_events = 4.

Output: results/sensitivity_declustering.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis.clustering import SeismicClusterAnalyzer, DEFAULT_MIN_MEAN_GC_KM
from src.analysis.declustering import GardnerKnopoffDeclustering, ZaliaipinDeclustering
from src.analysis.etas_validation import assign_fe_regions

CATALOG = ROOT / "data" / "processed" / "unified_catalog_full.csv"
OUT = ROOT / "results" / "sensitivity_declustering.json"

BASELINE_WINDOW = 2.0
BASELINE_MIN_EVENTS = 4


def _load_modern() -> pd.DataFrame:
    df = pd.read_csv(CATALOG, low_memory=False)
    df = df[(df["year"] >= 1973) & (df["magnitude"] >= 6.5)].copy()
    df = df.dropna(subset=["lat", "lon"])
    return assign_fe_regions(df)


def _count_series(df: pd.DataFrame) -> int:
    analyzer = SeismicClusterAnalyzer()
    series = analyzer.global_series(
        df,
        time_window_years=BASELINE_WINDOW,
        min_events=BASELINE_MIN_EVENTS,
        min_mean_gc_km=DEFAULT_MIN_MEAN_GC_KM,
    )
    return len(series)


def _apply_decluster(method: str, df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Return analysis catalog and number of dependent events removed."""
    if method == "gardner_knopoff":
        dec = GardnerKnopoffDeclustering()
        main, dep = dec.decluster(df)
        return main, len(dep)
    if method == "zaliapin":
        dec = ZaliaipinDeclustering()
        main, dep = dec.decluster(df)
        return main, len(dep)
    if method == "none":
        return df.copy(), 0
    raise ValueError(f"Unknown method: {method!r}")


def main() -> None:
    df_raw = _load_modern()
    n_raw = len(df_raw)

    configs = [
        ("gardner_knopoff", "GK (baseline)", "Gardner-Knopoff declustering (primary pipeline)"),
        ("zaliapin", "ZBZ", "Zaliapin-Ben-Zion declustering (pipeline_v2 decluster_method='zaliapin')"),
        ("none", "None", "No declustering; full M>=6.5 modern catalog"),
    ]

    rows: list[dict] = []
    for method_key, label, description in configs:
        catalog, n_removed = _apply_decluster(method_key, df_raw)
        n_series = _count_series(catalog)
        rows.append({
            "method": method_key,
            "label": label,
            "description": description,
            "n_events_input": n_raw,
            "n_events_after_decluster": len(catalog),
            "n_dependent_removed": n_removed,
            "time_window_years": BASELINE_WINDOW,
            "min_mean_gc_km": DEFAULT_MIN_MEAN_GC_KM,
            "min_events": BASELINE_MIN_EVENTS,
            "n_series_modern": n_series,
        })

    baseline_n = next(r["n_series_modern"] for r in rows if r["method"] == "gardner_knopoff")
    for row in rows:
        row["delta_vs_gk_baseline"] = row["n_series_modern"] - baseline_n

    out = {
        "catalog": "modern_1973_2026_M65",
        "n_events_raw": n_raw,
        "baseline_method": "gardner_knopoff",
        "baseline_n_series": baseline_n,
        "gates": {
            "time_window_years": BASELINE_WINDOW,
            "min_mean_gc_km": DEFAULT_MIN_MEAN_GC_KM,
            "min_events": BASELINE_MIN_EVENTS,
        },
        "methods": rows,
        "script": "scripts/run_declustering_sensitivity.py",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"Raw modern events: {n_raw}")
    print(f"Baseline GK N_series: {baseline_n}")
    for row in rows:
        print(
            f"  {row['label']:16s}  n_events={row['n_events_after_decluster']:4d}  "
            f"N_series={row['n_series_modern']:3d}  delta={row['delta_vs_gk_baseline']:+d}"
        )
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
