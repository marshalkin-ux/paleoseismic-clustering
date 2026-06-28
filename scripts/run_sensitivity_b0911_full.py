#!/usr/bin/env python
"""Full upstream pipeline at b=1.0 vs b=0.911 (GK + identify_clusters + global_series).

Re-runs identify_clusters() and global_series() on GK mainshocks for the modern
window. Compares N_series, Jaccard of series event sets, and upstream cluster
label mismatch fraction.

Output: results/sensitivity_b0911_full_pipeline.json
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
ETA_META = ROOT / "results" / "eta_threshold_meta.json"
OUT = ROOT / "results" / "sensitivity_b0911_full_pipeline.json"

TIME_WINDOW = 2.0
MIN_EVENTS = 4
B_VALUES = (1.0, 0.911)


def _load_modern() -> pd.DataFrame:
    df = pd.read_csv(CATALOG, low_memory=False)
    df = df[(df["year"] >= 1973) & (df["magnitude"] >= 6.5)].copy()
    df = df.dropna(subset=["lat", "lon"])
    return assign_fe_regions(df)


def _gk_mainshocks(df: pd.DataFrame) -> pd.DataFrame:
    gk = GardnerKnopoffDeclustering()
    main, _ = gk.decluster(df)
    return main.reset_index(drop=True)


def _eta0() -> float:
    default = 7.107191077237056e-06
    if ETA_META.exists():
        return float(
            json.loads(ETA_META.read_text(encoding="utf-8")).get("eta0_kde_valley", default)
        )
    return default


def _series_fingerprints(df: pd.DataFrame, b_param: float) -> set[tuple]:
    analyzer = SeismicClusterAnalyzer(b_param=b_param)
    series = analyzer.global_series(
        df,
        time_window_years=TIME_WINDOW,
        min_events=MIN_EVENTS,
        min_mean_gc_km=DEFAULT_MIN_MEAN_GC_KM,
    )
    fps: set[tuple] = set()
    for s in series:
        keys = tuple(
            sorted(
                (
                    int(r["year"]),
                    round(float(r["lat"]), 2),
                    round(float(r["lon"]), 2),
                )
                for _, r in s.iterrows()
            )
        )
        fps.add(keys)
    return fps


def _cluster_labels(df: pd.DataFrame, b_param: float, eta0: float) -> tuple[int, ...]:
    analyzer = SeismicClusterAnalyzer(b_param=b_param)
    nn = analyzer.find_nearest_neighbor(df)
    cl = analyzer.identify_clusters(nn, eta_threshold=eta0)
    return tuple(cl["cluster_id"].astype(int).tolist())


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


def main() -> None:
    df_raw = _load_modern()
    df_gk = _gk_mainshocks(df_raw)
    eta0 = _eta0()

    results_by_b: dict[str, dict] = {}
    fps_by_b: dict[float, set[tuple]] = {}
    labels_by_b: dict[float, tuple[int, ...]] = {}

    for b in B_VALUES:
        fps = _series_fingerprints(df_gk, b)
        labels = _cluster_labels(df_gk, b, eta0)
        fps_by_b[b] = fps
        labels_by_b[b] = labels
        results_by_b[str(b)] = {
            "b_param": b,
            "n_gk_mainshocks": len(df_gk),
            "n_series": len(fps),
            "n_cluster_labels": len(set(labels)),
            "eta0": eta0,
        }

    labels10 = labels_by_b[1.0]
    labels0911 = labels_by_b[0.911]
    n_mismatch = sum(1 for a, b in zip(labels10, labels0911) if a != b)

    fps10 = fps_by_b[1.0]
    fps0911 = fps_by_b[0.911]

    out = {
        "catalog": "modern_1973_2026_M65",
        "pipeline": "GK_mainshocks -> find_nearest_neighbor -> identify_clusters -> global_series",
        "n_events_raw": len(df_raw),
        "n_gk_mainshocks": len(df_gk),
        "gates": {
            "time_window_years": TIME_WINDOW,
            "min_mean_gc_km": DEFAULT_MIN_MEAN_GC_KM,
            "min_events": MIN_EVENTS,
        },
        "b_comparison": {
            "b_1.0": results_by_b["1.0"],
            "b_0.911": results_by_b["0.911"],
            "n_series_b1.0": len(fps10),
            "n_series_b0911": len(fps0911),
            "jaccard_series_event_sets": _jaccard(fps10, fps0911),
            "n_series_only_b1.0": len(fps10 - fps0911),
            "n_series_only_b0911": len(fps0911 - fps10),
        },
        "upstream_identify_clusters": {
            "eta0": eta0,
            "n_events_label_mismatch": n_mismatch,
            "fraction_label_mismatch": n_mismatch / len(df_gk) if len(df_gk) else 0.0,
        },
        "interpretation": (
            "Full GK pipeline re-run at b=0.911 vs b=1.0. "
            "global_series gates dominate N_series; upstream cluster labels differ."
        ),
        "script": "scripts/run_sensitivity_b0911_full.py",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
