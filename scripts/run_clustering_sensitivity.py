#!/usr/bin/env python
"""Parameter sensitivity for modern-window global-series detection (N_series).

Tests GC gate, sliding-window width, and catalog subset (GK mainshocks only).
Eta0 is documented from eta_threshold_meta.json (global_series path does not
apply eta0 directly — see note in output JSON).

Outputs:
    results/sensitivity_eta_windows_gc.json
    results/sensitivity_aftershock_removed.json  (GK mainshock-only subset)
    results/sensitivity_b_eta0.json  (b in eta metric; eta0 documented)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis.clustering import SeismicClusterAnalyzer, DEFAULT_MIN_MEAN_GC_KM
from src.analysis.declustering import GardnerKnopoffDeclustering
from src.analysis.etas_validation import assign_fe_regions

CATALOG = ROOT / "data" / "processed" / "unified_catalog_full.csv"
OUT_MAIN = ROOT / "results" / "sensitivity_eta_windows_gc.json"
OUT_AFTERSHOCK = ROOT / "results" / "sensitivity_aftershock_removed.json"
OUT_B_ETA0 = ROOT / "results" / "sensitivity_b_eta0.json"
B_CATALOG = 0.911
ETA_META = ROOT / "results" / "eta_threshold_meta.json"

BASELINE_WINDOW = 2.0
BASELINE_MIN_EVENTS = 4


def _load_modern() -> pd.DataFrame:
    df = pd.read_csv(CATALOG, low_memory=False)
    df = df[(df["year"] >= 1973) & (df["magnitude"] >= 6.5)].copy()
    df = df.dropna(subset=["lat", "lon"])
    return assign_fe_regions(df)


def _count_series(
    df: pd.DataFrame,
    *,
    time_window_years: float = BASELINE_WINDOW,
    min_mean_gc_km: float = DEFAULT_MIN_MEAN_GC_KM,
    min_events: int = BASELINE_MIN_EVENTS,
    b_param: float = 1.0,
) -> int:
    analyzer = SeismicClusterAnalyzer(b_param=b_param)
    series = analyzer.global_series(
        df,
        time_window_years=time_window_years,
        min_events=min_events,
        min_mean_gc_km=min_mean_gc_km,
    )
    return len(series)


def run_b_sensitivity(df: pd.DataFrame) -> list[dict]:
    rows = []
    for b_val, label in ((1.0, "default_bp2004"), (B_CATALOG, "catalog_mle_0.911")):
        rows.append({
            "parameter": "b_param_eta",
            "value": b_val,
            "label": label,
            "time_window_years": BASELINE_WINDOW,
            "min_mean_gc_km": DEFAULT_MIN_MEAN_GC_KM,
            "min_events": BASELINE_MIN_EVENTS,
            "n_series": _count_series(df, b_param=b_val),
            "baseline": b_val == 1.0,
        })
    return rows


def _gk_mainshocks(df: pd.DataFrame) -> pd.DataFrame:
    dec = GardnerKnopoffDeclustering()
    main, _dep = dec.decluster(df)
    return main


def run_gc_sensitivity(df: pd.DataFrame) -> list[dict]:
    rows = []
    for gc_km in (1000, 1500, 2000):
        rows.append({
            "parameter": "min_mean_gc_km",
            "value": gc_km,
            "time_window_years": BASELINE_WINDOW,
            "catalog": "full_modern",
            "n_series": _count_series(df, min_mean_gc_km=float(gc_km)),
            "baseline": gc_km == 1500,
        })
    return rows


def run_window_sensitivity(df: pd.DataFrame) -> list[dict]:
    rows = []
    configs = [
        ("single_1yr", [1.0]),
        ("single_2yr_baseline", [2.0]),
        ("single_5yr", [5.0]),
        ("single_10yr", [10.0]),
        ("set_125_baseline", [1.0, 2.0, 5.0]),
        ("set_2510", [2.0, 5.0, 10.0]),
    ]
    for label, windows in configs:
        counts = {
            str(w): _count_series(df, time_window_years=w) for w in windows
        }
        rows.append({
            "parameter": "time_window_years",
            "label": label,
            "windows": windows,
            "n_series_per_window": counts,
            "n_series_max_across_windows": max(counts.values()),
            "n_series_min_across_windows": min(counts.values()),
            "baseline": label == "single_2yr_baseline",
        })
    return rows


def run_aftershock_removed(df: pd.DataFrame) -> dict:
    main = _gk_mainshocks(df)
    full_n = _count_series(df)
    main_n = _count_series(main)
    return {
        "catalog": "modern_1973_2026_M65",
        "n_events_full": len(df),
        "n_events_gk_mainshocks": len(main),
        "n_gk_aftershocks_removed": len(df) - len(main),
        "time_window_years": BASELINE_WINDOW,
        "min_mean_gc_km": DEFAULT_MIN_MEAN_GC_KM,
        "min_events": BASELINE_MIN_EVENTS,
        "n_series_full_catalog": full_n,
        "n_series_gk_mainshocks_only": main_n,
        "delta_n_series": main_n - full_n,
        "note": (
            "GK mainshock-only subset removes local aftershocks before series "
            "detection; same global_series() gate as ETAS n_observed baseline."
        ),
    }


def _load_eta_meta() -> dict:
    if ETA_META.exists():
        with open(ETA_META, encoding="utf-8") as f:
            return json.load(f)
    return {}


def main() -> None:
    df = _load_modern()
    eta_meta = _load_eta_meta()
    eta0 = float(eta_meta.get("eta0_kde_valley", 7.107e-6))

    gc_rows = run_gc_sensitivity(df)
    window_rows = run_window_sensitivity(df)
    aftershock = run_aftershock_removed(df)
    b_rows = run_b_sensitivity(df)

    out = {
        "catalog": "modern_1973_2026_M65",
        "n_events": len(df),
        "baseline": {
            "time_window_years": BASELINE_WINDOW,
            "min_mean_gc_km": DEFAULT_MIN_MEAN_GC_KM,
            "min_events": BASELINE_MIN_EVENTS,
            "n_series": _count_series(df),
        },
        "gc_gate_sensitivity": gc_rows,
        "window_sensitivity": window_rows,
        "eta0_meta": {
            "eta0_kde_valley_default": eta0,
            "eta0_median_fallback": eta_meta.get("eta0_median_fallback"),
            "log10_eta0": eta_meta.get("log10_eta0"),
            "plus_20pct": eta0 * 1.2,
            "minus_20pct": eta0 * 0.8,
            "n_series_at_default_eta0": "not_applied",
            "note": (
                "ETAS/modern n_observed uses global_series() on the full event list "
                "without identify_clusters(eta0) filtering. Eta0 ±20% would affect "
                "the upstream NN-forest cluster step only; not re-run here — "
                "future work: pipeline_v2 with varied eta_threshold."
            ),
        },
        "aftershock_removed_summary": {
            "n_series_full": aftershock["n_series_full_catalog"],
            "n_series_gk_mainshocks": aftershock["n_series_gk_mainshocks_only"],
        },
        "script": "scripts/run_clustering_sensitivity.py",
    }

    b_eta0_out = {
        "catalog": "modern_1973_2026_M65",
        "n_events": len(df),
        "baseline_gates": {
            "time_window_years": BASELINE_WINDOW,
            "min_mean_gc_km": DEFAULT_MIN_MEAN_GC_KM,
            "min_events": BASELINE_MIN_EVENTS,
        },
        "b_param_sensitivity": b_rows,
        "eta0_sensitivity": {
            "eta0_kde_valley_default": eta0,
            "plus_20pct": eta0 * 1.2,
            "minus_20pct": eta0 * 0.8,
            "n_series_at_default_eta0": "not_applied",
            "n_series_at_plus_20pct": "not_applied",
            "n_series_at_minus_20pct": "not_applied",
            "note": (
                "global_series() does not apply eta0 filtering; eta0 ±20% would "
                "affect upstream identify_clusters() only — not re-run here."
            ),
        },
        "window_sensitivity_ref": "results/sensitivity_eta_windows_gc.json",
        "script": "scripts/run_clustering_sensitivity.py",
    }

    OUT_MAIN.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_MAIN, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    with open(OUT_AFTERSHOCK, "w", encoding="utf-8") as f:
        json.dump(aftershock, f, indent=2, ensure_ascii=False)
    with open(OUT_B_ETA0, "w", encoding="utf-8") as f:
        json.dump(b_eta0_out, f, indent=2, ensure_ascii=False)

    print(f"Baseline N_series (GC>{DEFAULT_MIN_MEAN_GC_KM:.0f} km, 2 yr): {out['baseline']['n_series']}")
    for row in gc_rows:
        print(f"  GC {row['value']} km -> N={row['n_series']}")
    for row in b_rows:
        print(f"  b={row['value']} ({row['label']}) -> N={row['n_series']}")
    print(f"GK mainshocks only: N={aftershock['n_series_gk_mainshocks_only']} (full={aftershock['n_series_full_catalog']})")
    print(f"Saved {OUT_MAIN}")
    print(f"Saved {OUT_AFTERSHOCK}")
    print(f"Saved {OUT_B_ETA0}")


if __name__ == "__main__":
    main()
