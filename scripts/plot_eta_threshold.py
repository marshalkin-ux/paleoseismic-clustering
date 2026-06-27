#!/usr/bin/env python
"""Plot nearest-neighbor log10(eta) distribution with KDE valley threshold eta0.

Outputs figures/grl/fig_eta_threshold.png (GRL light style, matches fig02).

Usage
-----
    python scripts/plot_eta_threshold.py
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
from scipy.signal import argrelmin
from scipy.stats import gaussian_kde

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis.clustering import SeismicClusterAnalyzer
from src.analysis.declustering import GardnerKnopoffDeclustering, ZaliaipinDeclustering
from src.analysis.tectonic_distance import TectonicDistanceCalculator

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

OUT = ROOT / "figures" / "grl"
META = ROOT / "results" / "eta_threshold_meta.json"

GRL_RC = {
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "axes.edgecolor": "#333333",
    "axes.labelcolor": "#222222",
    "xtick.color": "#333333",
    "ytick.color": "#333333",
    "text.color": "#222222",
    "grid.color": "#cccccc",
    "grid.alpha": 0.6,
    "font.family": "DejaVu Sans",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.dpi": 300,
    "savefig.facecolor": "white",
}

THRESH_COLOR = "#c0392b"
KDE_COLOR = "#2980b9"
HIST_COLOR = "#5dade2"


def _load_modern_mainshocks() -> pd.DataFrame:
    catalog_path = ROOT / "data" / "processed" / "unified_catalog_full.csv"
    df = pd.read_csv(catalog_path)
    df = df[df["year"] >= 1973].copy()
    df = df[df["magnitude"] >= 6.5].copy()
    df = df.sort_values(["year", "month", "day"]).reset_index(drop=True)
    gk = GardnerKnopoffDeclustering()
    mainshocks, _ = gk.decluster(df)
    return mainshocks.sort_values(["year", "month", "day"]).reset_index(drop=True)


def _compute_nn_etas(events: pd.DataFrame) -> np.ndarray:
    dist_calc = TectonicDistanceCalculator()
    analyzer = SeismicClusterAnalyzer(dist_calculator=dist_calc)
    df_nn = analyzer.find_nearest_neighbor(events, dist_calculator=dist_calc)
    etas = df_nn["eta"].to_numpy(dtype=float)
    return etas[np.isfinite(etas) & (etas > 0)]


def plot_eta_threshold(
    eta_values: np.ndarray,
    eta0: float,
    output_path: Path,
) -> None:
    log_eta = np.log10(eta_values)
    log_eta0 = float(np.log10(eta0))

    plt.rcParams.update(GRL_RC)
    fig, ax = plt.subplots(figsize=(9, 5.5))

    ax.hist(
        log_eta,
        bins=60,
        density=True,
        alpha=0.45,
        color=HIST_COLOR,
        edgecolor="white",
        linewidth=0.4,
        label="Nearest-neighbor log₁₀(η)",
    )

    x_grid = np.linspace(log_eta.min(), log_eta.max(), 500)
    kde = gaussian_kde(log_eta, bw_method=0.15)
    density = kde(x_grid)
    ax.plot(x_grid, density, color=KDE_COLOR, lw=2.2, label="KDE (Silverman bw=0.15)")

    mins_idx = argrelmin(density, order=10)[0]
    if len(mins_idx) > 0:
        peaks_idx = np.argsort(density)[::-1]
        if len(peaks_idx) >= 2:
            p1, p2 = sorted([peaks_idx[0], peaks_idx[1]])
            between = mins_idx[(mins_idx > p1) & (mins_idx < p2)]
            if len(between) > 0:
                valley_idx = between[np.argmin(density[between])]
                ax.scatter(
                    x_grid[valley_idx],
                    density[valley_idx],
                    s=60,
                    c=THRESH_COLOR,
                    zorder=5,
                    label="KDE valley",
                )

    ax.axvline(
        log_eta0,
        color=THRESH_COLOR,
        lw=2,
        ls="--",
        label=f"η₀ = {eta0:.2e} (log₁₀ = {log_eta0:.2f})",
    )

    ax.set_xlabel("log₁₀(η) — nearest-neighbor metric (1973–2026, GK mainshocks)")
    ax.set_ylabel("Density")
    ax.set_title(
        "Nearest-neighbor η distribution and Zaliapin–Ben-Zion threshold η₀\n"
        f"n = {len(eta_values)} events; b = 1.0, r^1.6 (Baiesi–Paczuski 2004)"
    )
    ax.legend(loc="upper right", framealpha=0.95)
    ax.grid(True, alpha=0.35)
    fig.tight_layout()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    logger.info("Saved %s", output_path)


def main() -> None:
    events = _load_modern_mainshocks()
    logger.info("Modern GK mainshocks: %d", len(events))

    etas = _compute_nn_etas(events)
    zbz = ZaliaipinDeclustering()
    eta0 = zbz.find_threshold_kde(etas)
    median_eta0 = float(10 ** np.median(np.log10(etas)))

    out_png = OUT / "fig_eta_threshold.png"
    plot_eta_threshold(etas, eta0, out_png)

    meta = {
        "n_events": int(len(etas)),
        "eta0_kde_valley": float(eta0),
        "eta0_median_fallback": median_eta0,
        "log10_eta0": float(np.log10(eta0)),
        "catalog": "data/processed/unified_catalog_full.csv",
        "window": "1973-2026",
        "declustering": "Gardner-Knopoff",
        "figure": str(out_png.relative_to(ROOT)).replace("\\", "/"),
        "script": "scripts/plot_eta_threshold.py",
    }
    META.parent.mkdir(parents=True, exist_ok=True)
    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Saved %s", META)
    logger.info("eta0 (KDE valley) = %.4e; median fallback = %.4e", eta0, median_eta0)


if __name__ == "__main__":
    main()
