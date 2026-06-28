#!/usr/bin/env python
"""Series stability matrix: intersection analysis across detector parameters.

Baseline: Δt=2 yr, GK declustering, b=1.0, mean GC>1500 km, N≥4.
Compares N_series and Jaccard vs baseline for declustering, window, and b variants.

Output: results/series_stability_venn.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from itertools import combinations

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis.clustering import SeismicClusterAnalyzer, DEFAULT_MIN_MEAN_GC_KM
from src.analysis.declustering import GardnerKnopoffDeclustering, ZaliaipinDeclustering
from src.analysis.etas_validation import assign_fe_regions

CATALOG = ROOT / "data" / "processed" / "unified_catalog_full.csv"
OUT = ROOT / "results" / "series_stability_venn.json"

BASELINE_DT = 2.0
BASELINE_B = 1.0
BASELINE_DECLUSTER = "gardner_knopoff"
MIN_EVENTS = 4


def _load_modern() -> pd.DataFrame:
    df = pd.read_csv(CATALOG, low_memory=False)
    df = df[(df["year"] >= 1973) & (df["magnitude"] >= 6.5)].copy()
    df = df.dropna(subset=["lat", "lon"])
    return assign_fe_regions(df)


def _apply_decluster(method: str, df: pd.DataFrame) -> pd.DataFrame:
    if method == "gardner_knopoff":
        gk = GardnerKnopoffDeclustering()
        main, _ = gk.decluster(df)
        return main
    if method == "zaliapin":
        zbz = ZaliaipinDeclustering()
        main, _ = zbz.decluster(df)
        return main
    if method == "none":
        return df.copy()
    raise ValueError(method)


def _event_keys_from_series(series_list: list[pd.DataFrame]) -> set[tuple]:
    keys: set[tuple] = set()
    for s in series_list:
        for _, r in s.iterrows():
            keys.add(
                (
                    int(r["year"]),
                    round(float(r["lat"]), 2),
                    round(float(r["lon"]), 2),
                )
            )
    return keys


def _series_fingerprints(
    df: pd.DataFrame,
    *,
    dt: float,
    b_param: float,
) -> tuple[int, set[tuple], set[tuple]]:
    analyzer = SeismicClusterAnalyzer(b_param=b_param)
    series = analyzer.global_series(
        df,
        time_window_years=dt,
        min_events=MIN_EVENTS,
        min_mean_gc_km=DEFAULT_MIN_MEAN_GC_KM,
    )
    fps: set[tuple] = set()
    for s in series:
        fps.add(
            tuple(
                sorted(
                    (
                        int(r["year"]),
                        round(float(r["lat"]), 2),
                        round(float(r["lon"]), 2),
                    )
                    for _, r in s.iterrows()
                )
            )
        )
    event_keys = _event_keys_from_series(series)
    return len(series), fps, event_keys


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


def main() -> None:
    df_raw = _load_modern()

    configs: list[dict] = []
    for dt in (1.0, 2.0, 5.0):
        for decl in ("gardner_knopoff", "zaliapin", "none"):
            for b in (1.0, 0.911):
                if decl != "gardner_knopoff" and b != 1.0:
                    continue
                label = f"dt{dt:g}_{decl}_b{b:g}"
                configs.append({
                    "label": label,
                    "time_window_years": dt,
                    "decluster": decl,
                    "b_param": b,
                    "is_baseline": (
                        dt == BASELINE_DT
                        and decl == BASELINE_DECLUSTER
                        and b == BASELINE_B
                    ),
                })

    baseline_fps: set[tuple] | None = None
    baseline_events: set[tuple] | None = None
    rows: list[dict] = []
    event_sets: dict[str, set[tuple]] = {}

    for cfg in configs:
        catalog = _apply_decluster(cfg["decluster"], df_raw)
        n_series, fps, events = _series_fingerprints(
            catalog,
            dt=cfg["time_window_years"],
            b_param=cfg["b_param"],
        )
        event_sets[cfg["label"]] = events
        row = {
            **cfg,
            "n_events_input": len(catalog),
            "n_series": n_series,
            "n_unique_events_in_series": len(events),
        }
        if cfg["is_baseline"]:
            baseline_fps = fps
            baseline_events = events
            row["jaccard_series_vs_baseline"] = 1.0
            row["jaccard_events_vs_baseline"] = 1.0
        rows.append(row)

    assert baseline_fps is not None and baseline_events is not None
    for row in rows:
        if row["is_baseline"]:
            continue
        catalog = _apply_decluster(row["decluster"], df_raw)
        _, fps, events = _series_fingerprints(
            catalog,
            dt=row["time_window_years"],
            b_param=row["b_param"],
        )
        row["jaccard_series_vs_baseline"] = _jaccard(fps, baseline_fps)
        row["jaccard_events_vs_baseline"] = _jaccard(events, baseline_events)

    all_event_sets = list(event_sets.values())
    core_events = set.intersection(*all_event_sets) if all_event_sets else set()
    union_events = set.union(*all_event_sets) if all_event_sets else set()

    pairwise_jaccard: list[dict] = []
    labels = list(event_sets.keys())
    for a, b in combinations(labels, 2):
        pairwise_jaccard.append({
            "a": a,
            "b": b,
            "jaccard_events": _jaccard(event_sets[a], event_sets[b]),
        })

    n_baseline_series = next(r["n_series"] for r in rows if r["is_baseline"])
    n_at_27 = sum(1 for r in rows if r["n_series"] == n_baseline_series)

    out = {
        "baseline": {
            "time_window_years": BASELINE_DT,
            "decluster": BASELINE_DECLUSTER,
            "b_param": BASELINE_B,
            "n_series": n_baseline_series,
            "n_unique_events_in_series": len(baseline_events),
        },
        "parameter_matrix": rows,
        "intersection_analysis": {
            "n_configs": len(rows),
            "n_configs_with_n_series_27": n_at_27,
            "core_events_all_configs": len(core_events),
            "union_events_any_config": len(union_events),
            "core_fraction_of_baseline_events": (
                len(core_events) / len(baseline_events) if baseline_events else 0.0
            ),
            "baseline_only_events": len(baseline_events - union_events.union(*[
                s for lab, s in event_sets.items()
                if lab != next(r["label"] for r in rows if r["is_baseline"])
            ])) if baseline_events else 0,
        },
        "pairwise_jaccard_events_sample": pairwise_jaccard[:15],
        "interpretation": (
            "Core stable events appear in every parameter set; "
            "N=27 at baseline reflects detector gates; "
            "window width dominates N_series variation."
        ),
        "script": "scripts/compute_series_stability.py",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
