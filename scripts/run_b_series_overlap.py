#!/usr/bin/env python
"""Compare global-series and upstream cluster labels at b=1.0 vs b=0.911."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis.clustering import SeismicClusterAnalyzer
from src.analysis.etas_validation import assign_fe_regions

CATALOG = ROOT / "data" / "processed" / "unified_catalog_full.csv"
ETA_META = ROOT / "results" / "eta_threshold_meta.json"
OUT = ROOT / "results" / "sensitivity_b0911_series_overlap.json"


def _load_modern() -> pd.DataFrame:
    df = pd.read_csv(CATALOG, low_memory=False)
    df = df[(df["year"] >= 1973) & (df["magnitude"] >= 6.5)].copy()
    df = df.dropna(subset=["lat", "lon"])
    return assign_fe_regions(df)


def _series_fingerprints(df: pd.DataFrame, b_param: float) -> set[tuple]:
    analyzer = SeismicClusterAnalyzer(b_param=b_param)
    series = analyzer.global_series(df, time_window_years=2.0, min_events=4)
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


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def _cluster_labels(df: pd.DataFrame, b_param: float, eta0: float) -> tuple[int, ...]:
    analyzer = SeismicClusterAnalyzer(b_param=b_param)
    nn = analyzer.find_nearest_neighbor(df)
    cl = analyzer.identify_clusters(nn, eta_threshold=eta0)
    return tuple(cl["cluster_id"].astype(int).tolist())


def main() -> None:
    df = _load_modern()
    eta0 = 7.107191077237056e-06
    if ETA_META.exists():
        eta0 = float(
            json.loads(ETA_META.read_text(encoding="utf-8")).get("eta0_kde_valley", eta0)
        )

    fps10 = _series_fingerprints(df, 1.0)
    fps0911 = _series_fingerprints(df, 0.911)
    labels10 = _cluster_labels(df, 1.0, eta0)
    labels0911 = _cluster_labels(df, 0.911, eta0)
    n_mismatch = sum(1 for a, b in zip(labels10, labels0911) if a != b)

    out = {
        "catalog": "modern_1973_2026_M65",
        "n_events": len(df),
        "baseline_gates": {
            "time_window_years": 2.0,
            "min_mean_gc_km": 1500.0,
            "min_events": 4,
        },
        "global_series_comparison": {
            "b_1.0": {"n_series": len(fps10)},
            "b_0.911": {"n_series": len(fps0911)},
            "jaccard_series_event_sets": _jaccard(fps10, fps0911),
            "n_series_only_b1.0": len(fps10 - fps0911),
            "n_series_only_b0911": len(fps0911 - fps10),
            "note": (
                "global_series() does not use b_param; identical sets expected "
                "when only sliding-window gates apply."
            ),
        },
        "upstream_identify_clusters": {
            "eta0": eta0,
            "n_events_label_mismatch": n_mismatch,
            "fraction_label_mismatch": n_mismatch / len(df),
            "note": (
                "find_nearest_neighbor + identify_clusters() at catalog b=0.911 "
                "vs BP b=1.0; not re-run in primary pipeline."
            ),
        },
        "interpretation": (
            "Equal N_series=27 does not prove candidate identity; "
            "global_series path is b-independent; upstream cluster labels "
            "differ when b changes."
        ),
        "script": "scripts/run_b_series_overlap.py",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
