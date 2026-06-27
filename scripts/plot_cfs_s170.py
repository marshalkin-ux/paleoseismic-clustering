#!/usr/bin/env python
"""Plot ΔCFS results for S170 post-Sumatra receivers (fig06_cfs_s170.png)."""

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

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

OUT = ROOT / "figures" / "grl"
OUT.mkdir(parents=True, exist_ok=True)


def plot_cfs_s170() -> Path:
    json_path = ROOT / "results" / "cfs_s170_analysis.json"
    csv_path = ROOT / "results" / "cfs_s170_events.csv"
    if not json_path.exists():
        raise FileNotFoundError("Run scripts/compute_cfs_s170.py first")

    with open(json_path, encoding="utf-8") as f:
        analysis = json.load(f)
    df = pd.read_csv(csv_path)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), facecolor="white")

    # Panel A: regional bar chart (mean ± range)
    regions = ["Japan", "Aleutians"]
    colors = {"Japan": "#2563eb", "Aleutians": "#e63946"}
    means = []
    medians = []
    for reg in regions:
        sub = df[df["region"] == reg]
        means.append(sub["dcfs_kpa"].mean() if len(sub) else 0)
        medians.append(sub["dcfs_kpa"].median() if len(sub) else 0)

    x = np.arange(len(regions))
    bars = axes[0].bar(x, means, color=[colors[r] for r in regions], alpha=0.85, edgecolor="white")
    axes[0].axhline(0, color="#333", lw=0.8)
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(regions)
    axes[0].set_ylabel("Mean ΔCFS (kPa)")
    axes[0].set_title("Post-Sumatra 2004 static ΔCFS\n(S170 receivers, μ=0.4)")
    for i, (bar, med) in enumerate(zip(bars, medians)):
        axes[0].text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"n={len(df[df['region']==regions[i]])}\nmed={med:.3f}",
            ha="center",
            va="bottom" if bar.get_height() >= 0 else "top",
            fontsize=8,
        )

    # Panel B: map-style scatter (lon/lat coloured by ΔCFS sign)
    for reg in regions:
        sub = df[df["region"] == reg]
        if sub.empty:
            continue
        sc = axes[1].scatter(
            sub["lon"],
            sub["lat"],
            c=sub["dcfs_kpa"],
            cmap="RdBu_r",
            s=40 + 20 * (sub["magnitude"] - 6.5),
            vmin=-np.abs(df["dcfs_kpa"]).max(),
            vmax=np.abs(df["dcfs_kpa"]).max(),
            edgecolors="k",
            linewidths=0.3,
            label=reg,
            alpha=0.85,
        )
    axes[1].scatter(
        [analysis["source_parameters"]["lon"]],
        [analysis["source_parameters"]["lat"]],
        marker="*",
        s=200,
        c="gold",
        edgecolors="k",
        zorder=5,
        label="Sumatra 2004",
    )
    plt.colorbar(sc, ax=axes[1], label="ΔCFS (kPa)", shrink=0.85)
    axes[1].set_xlabel("Longitude")
    axes[1].set_ylabel("Latitude")
    axes[1].set_title("Receiver locations\n(red = promoting, blue = inhibiting)")
    axes[1].legend(loc="lower left", fontsize=8)
    axes[1].grid(True, linestyle="--", alpha=0.4)

    jp = analysis["summary_by_region"]["Japan"]
    al = analysis["summary_by_region"]["Aleutians"]
    jp_mean = jp.get("mean_dcfs_kpa") or 0.0
    al_mean = al.get("mean_dcfs_kpa") or 0.0
    jp_pct = jp.get("pct_promoting") or 0.0
    al_pct = al.get("pct_promoting") or 0.0
    fig.suptitle(
        f"S170 Coulomb stress after Sumatra 2004 M9.1  |  "
        f"Japan: {jp_mean:.3f} kPa ({jp_pct:.0f}% promoting)  |  "
        f"Aleutians: {al_mean:.3f} kPa ({al_pct:.0f}% promoting)",
        fontsize=9,
        y=1.02,
    )
    fig.tight_layout()
    out_path = OUT / "fig06_cfs_s170.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    logger.info("Saved %s", out_path)
    return out_path


if __name__ == "__main__":
    plot_cfs_s170()
