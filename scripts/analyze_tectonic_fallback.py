#!/usr/bin/env python
"""Analyse tectonic-path vs 1.5× great-circle fallback usage.

Samples event pairs from the unified catalog, classifies each pair as using
a real Dijkstra path on the Bird (2003) boundary graph or the 1.5×GC fallback,
and reports regional differences.

Outputs
-------
    results/tectonic_fallback_analysis.json
    figures/grl/fig07_tectonic_path_usage.png
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis.tectonic_distance_v2 import TectonicDistanceV2, _haversine_km

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

OUT_JSON = ROOT / "results" / "tectonic_fallback_analysis.json"
OUT_FIG = ROOT / "figures" / "grl" / "fig07_tectonic_path_usage.png"


def classify_pair(
    calc: TectonicDistanceV2,
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    max_boundary_dist_km: float = 500.0,
) -> dict:
    """Return distance metrics and whether Dijkstra path or GC fallback was used."""
    if calc._graph is None:
        calc.build_graph()

    gc_km = _haversine_km(lat1, lon1, lat2, lon2)
    fallback_km = gc_km * 1.5

    n1 = calc._nearest_node(lat1, lon1)
    n2 = calc._nearest_node(lat2, lon2)
    d1 = _haversine_km(lat1, lon1, *calc._node_coords[n1])
    d2 = _haversine_km(lat2, lon2, *calc._node_coords[n2])

    used_fallback = False
    reason = "dijkstra"
    tect_km = fallback_km

    if d1 > max_boundary_dist_km or d2 > max_boundary_dist_km:
        used_fallback = True
        reason = "snap_distance_exceeded"
    else:
        import networkx as nx
        try:
            path_len = nx.dijkstra_path_length(calc._graph, n1, n2, weight="weight")
            tect_km = float(d1 + path_len + d2)
        except nx.NetworkXNoPath:
            used_fallback = True
            reason = "no_graph_path"

    if used_fallback:
        tect_km = fallback_km

    ratio = tect_km / gc_km if gc_km > 0 else np.nan
    material_diff = abs(tect_km - fallback_km) / fallback_km if fallback_km > 0 else 0.0

    return {
        "gc_km": float(gc_km),
        "tectonic_km": float(tect_km),
        "fallback_km": float(fallback_km),
        "used_dijkstra": not used_fallback,
        "used_fallback": used_fallback,
        "fallback_reason": reason,
        "ratio_tect_gc": float(ratio),
        "material_diff_from_fallback": float(material_diff),
        "snap_d1_km": float(d1),
        "snap_d2_km": float(d2),
    }


def main() -> None:
    catalog_path = ROOT / "data" / "processed" / "unified_catalog_full.csv"
    df = pd.read_csv(catalog_path)
    # Modern instrumental sample (same window as clustering)
    df = df[df["year"] >= 1973].copy()
    rng = np.random.default_rng(42)
    n_sample = min(500, len(df))
    sample = df.sample(n=n_sample, random_state=42).reset_index(drop=True)

    calc = TectonicDistanceV2()
    calc.build_graph()

    pairs = []
    n_pairs = min(5000, n_sample * (n_sample - 1) // 2)
    idx_i = rng.integers(0, n_sample, size=n_pairs)
    idx_j = rng.integers(0, n_sample, size=n_pairs)
    mask = idx_i != idx_j
    idx_i, idx_j = idx_i[mask], idx_j[mask]

    for i, j in zip(idx_i, idx_j):
        r1, r2 = sample.iloc[i], sample.iloc[j]
        info = classify_pair(calc, r1["lat"], r1["lon"], r2["lat"], r2["lon"])
        info.update({
            "event_id_1": r1["event_id"],
            "event_id_2": r2["event_id"],
            "lat1": float(r1["lat"]),
            "lon1": float(r1["lon"]),
            "lat2": float(r2["lat"]),
            "lon2": float(r2["lon"]),
            "region1": str(r1.get("fe_region", r1.get("region", ""))),
            "region2": str(r2.get("fe_region", r2.get("region", ""))),
        })
        pairs.append(info)

    pairs_df = pd.DataFrame(pairs)
    n_total = len(pairs_df)
    n_dijkstra = int(pairs_df["used_dijkstra"].sum())
    n_fallback = int(pairs_df["used_fallback"].sum())
    pct_dijkstra = 100.0 * n_dijkstra / n_total
    pct_fallback = 100.0 * n_fallback / n_total

    # Pairs where tectonic path differs materially from fallback (>5% relative)
    material = pairs_df[
        pairs_df["used_dijkstra"] & (pairs_df["material_diff_from_fallback"] > 0.05)
    ].sort_values("material_diff_from_fallback", ascending=False)

    material_records = material.head(30).to_dict(orient="records")

    by_reason = pairs_df.groupby("fallback_reason").size().to_dict()

    summary = {
        "n_events_sampled": n_sample,
        "n_pairs": n_total,
        "pct_real_dijkstra_path": round(pct_dijkstra, 2),
        "pct_gc_fallback_1p5x": round(pct_fallback, 2),
        "fallback_by_reason": by_reason,
        "median_ratio_tect_gc_dijkstra_only": float(
            pairs_df.loc[pairs_df["used_dijkstra"], "ratio_tect_gc"].median()
        ),
        "n_materially_different_dijkstra_pairs": int(len(material)),
        "material_different_examples": material_records,
        "method": "TectonicDistanceV2, max_boundary_dist_km=500, fallback=1.5×GC",
        "random_seed": 42,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    logger.info("Saved %s", OUT_JSON)
    logger.info("Dijkstra: %.1f%%  Fallback: %.1f%%", pct_dijkstra, pct_fallback)

    # Figure
    OUT_FIG.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), facecolor="white")

    axes[0].pie(
        [n_dijkstra, n_fallback],
        labels=[f"Dijkstra path\n({pct_dijkstra:.1f}%)", f"1.5× GC fallback\n({pct_fallback:.1f}%)"],
        colors=["#27ae60", "#95a5a6"],
        autopct="%1.1f%%",
        startangle=90,
    )
    axes[0].set_title(f"Tectonic distance method\n(n={n_total} random pairs, 1973+)")

    dij = pairs_df[pairs_df["used_dijkstra"]]["ratio_tect_gc"]
    fb = pairs_df[pairs_df["used_fallback"]]["ratio_tect_gc"]
    axes[1].hist(dij, bins=40, alpha=0.75, label=f"Dijkstra (n={len(dij)})", color="#27ae60")
    axes[1].axvline(1.5, color="#e63946", ls="--", lw=1.5, label="1.5× GC (fallback)")
    axes[1].set_xlabel("Tectonic / great-circle ratio")
    axes[1].set_ylabel("Pair count")
    axes[1].set_title("Path-length ratio distribution")
    axes[1].legend(fontsize=8)
    axes[1].grid(axis="y", linestyle="--", alpha=0.4)

    fig.suptitle(
        f"Tectonic distance fallback audit  |  {pct_dijkstra:.1f}% real Dijkstra  |  "
        f"{pct_fallback:.1f}% 1.5×GC fallback",
        fontsize=9,
        y=1.02,
    )
    fig.tight_layout()
    fig.savefig(OUT_FIG, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    logger.info("Saved %s", OUT_FIG)


if __name__ == "__main__":
    main()
