#!/usr/bin/env python
"""Compute dynamic stress for Japan receivers after Sumatra 2004 M9.1.

Connects S170 Japan-region events to teleseismic Rayleigh/Love surface-wave
physics and Hill et al. (1993) / Gomberg (2001) dynamic stress conversion.

Assumptions (see results/dynamic_stress_note.md)
------------------------------------------------
* Source: point Brune/Boatwright spectrum, Mw 9.1 at 3.3°N, 95.8°E.
* Receivers: Japan (lat 30–45°N, lon 130–145°E), distance 4000–5500 km,
  from S170 members or catalog (M≥6.5, 2004–2016).
* Surface-wave spreading 1/sqrt(r); Q=350–450, U=3.5–4.0 km/s.
* σ_dyn = μ·PGV/β (μ=30 GPa, β=3.5 km/s).
* No site amplification, directivity, or finite-fault propagation effects.

Outputs
-------
    results/dynamic_stress_sumatra2004.json
    figures/grl/fig08_dynamic_stress_japan.png
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

from scripts.compute_cfs_s170 import load_catalog_receivers, load_s170_event_ids
from src.analysis.dynamic_stress import (
    SUMATRA_2004_LAT,
    SUMATRA_2004_LON,
    SUMATRA_2004_MW,
    THRESHOLD_SIGMA_HIGH_MPA,
    THRESHOLD_SIGMA_LOW_MPA,
    batch_dynamic_stress,
    default_love_band,
    default_rayleigh_band,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

JAPAN_LAT_MIN, JAPAN_LAT_MAX = 30.0, 45.0
JAPAN_LON_MIN, JAPAN_LON_MAX = 130.0, 145.0
DIST_MIN_KM, DIST_MAX_KM = 4000.0, 6500.0


def filter_japan_receivers(receivers_df: pd.DataFrame) -> pd.DataFrame:
    """Japan box + teleseismic distance window."""
    mask = (
        (receivers_df["region_group"] == "Japan")
        & (receivers_df["lat"] >= JAPAN_LAT_MIN)
        & (receivers_df["lat"] <= JAPAN_LAT_MAX)
        & (receivers_df["lon"] >= JAPAN_LON_MIN)
        & (receivers_df["lon"] <= JAPAN_LON_MAX)
    )
    return receivers_df[mask].copy()


def _summary_stats(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "n": 0,
            "mean_pgv_max_cm_s": None,
            "median_pgv_max_cm_s": None,
            "mean_sigma_dyn_max_mpa": None,
            "median_sigma_dyn_max_mpa": None,
            "min_sigma_dyn_max_mpa": None,
            "max_sigma_dyn_max_mpa": None,
            "pct_exceeds_0_01_mpa": None,
            "pct_exceeds_0_1_mpa": None,
        }
    return {
        "n": int(len(df)),
        "mean_pgv_max_cm_s": float(df["pgv_max_cm_s"].mean()),
        "median_pgv_max_cm_s": float(df["pgv_max_cm_s"].median()),
        "mean_sigma_dyn_max_mpa": float(df["sigma_dyn_max_mpa"].mean()),
        "median_sigma_dyn_max_mpa": float(df["sigma_dyn_max_mpa"].median()),
        "min_sigma_dyn_max_mpa": float(df["sigma_dyn_max_mpa"].min()),
        "max_sigma_dyn_max_mpa": float(df["sigma_dyn_max_mpa"].max()),
        "pct_exceeds_0_01_mpa": float(100.0 * df["exceeds_0_01_mpa"].mean()),
        "pct_exceeds_0_1_mpa": float(100.0 * df["exceeds_0_1_mpa"].mean()),
    }


def plot_dynamic_stress(df: pd.DataFrame, analysis: dict, out_path: Path) -> None:
    """Distance vs σ_dyn with literature threshold lines."""
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), facecolor="white")

    # Panel A: distance vs dynamic stress
    ax = axes[0]
    ax.scatter(
        df["distance_km"],
        df["sigma_dyn_rayleigh_mpa"],
        c="#2563eb",
        s=35,
        alpha=0.75,
        label="Rayleigh",
        edgecolors="k",
        linewidths=0.2,
    )
    ax.scatter(
        df["distance_km"],
        df["sigma_dyn_love_mpa"],
        c="#e63946",
        s=35,
        alpha=0.75,
        label="Love",
        edgecolors="k",
        linewidths=0.2,
    )
    ax.axhline(
        THRESHOLD_SIGMA_LOW_MPA,
        color="#f59e0b",
        ls="--",
        lw=1.2,
        label=f"{THRESHOLD_SIGMA_LOW_MPA} MPa (10 kPa)",
    )
    ax.axhline(
        THRESHOLD_SIGMA_HIGH_MPA,
        color="#dc2626",
        ls="--",
        lw=1.2,
        label=f"{THRESHOLD_SIGMA_HIGH_MPA} MPa (100 kPa)",
    )
    ax.set_xlabel("Epicentral distance (km)")
    ax.set_ylabel("Peak dynamic stress σ_dyn (MPa)")
    ax.set_title("Dynamic stress vs distance\n(Sumatra 2004 → Japan receivers)")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.set_xlim(DIST_MIN_KM - 100, DIST_MAX_KM + 200)
    # Data are orders of magnitude below literature thresholds — use log scale
    positive = df["sigma_dyn_max_mpa"].replace(0, np.nan).dropna()
    if len(positive):
        ax.set_yscale("log")
        ymin = max(positive.min() * 0.5, 1e-7)
        ax.set_ylim(ymin, THRESHOLD_SIGMA_HIGH_MPA * 2)

    # Panel B: map
    ax2 = axes[1]
    sc = ax2.scatter(
        df["lon"],
        df["lat"],
        c=df["sigma_dyn_max_mpa"],
        cmap="YlOrRd",
        s=40 + 15 * (df["magnitude"] - 6.5),
        vmin=0,
        vmax=max(df["sigma_dyn_max_mpa"].max(), THRESHOLD_SIGMA_LOW_MPA * 1.5),
        edgecolors="k",
        linewidths=0.3,
    )
    ax2.scatter(
        [SUMATRA_2004_LON],
        [SUMATRA_2004_LAT],
        marker="*",
        s=200,
        c="gold",
        edgecolors="k",
        zorder=5,
        label="Sumatra 2004",
    )
    plt.colorbar(sc, ax=ax2, label="σ_dyn max (MPa)", shrink=0.85)
    ax2.set_xlabel("Longitude")
    ax2.set_ylabel("Latitude")
    ax2.set_title("Japan receivers coloured by σ_dyn")
    ax2.set_xlim(JAPAN_LON_MIN - 1, JAPAN_LON_MAX + 1)
    ax2.set_ylim(JAPAN_LAT_MIN - 1, JAPAN_LAT_MAX + 1)
    ax2.grid(True, linestyle="--", alpha=0.35)
    ax2.legend(loc="lower left", fontsize=8)

    s = analysis["summary"]
    fig.suptitle(
        f"Dynamic stress after Sumatra 2004 M9.1  |  n={s['n']}  |  "
        f"median σ_dyn={s['median_sigma_dyn_max_mpa']:.4f} MPa  |  "
        f"{s['pct_exceeds_0_01_mpa']:.0f}% ≥ 0.01 MPa",
        fontsize=9,
        y=1.02,
    )
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    logger.info("Saved %s", out_path)


def main() -> None:
    catalog_path = ROOT / "data" / "processed" / "unified_catalog_full.csv"
    if not catalog_path.exists():
        logger.error("Catalog not found: %s", catalog_path)
        sys.exit(1)

    event_ids = load_s170_event_ids()
    catalog = pd.read_csv(catalog_path)
    receivers_df = load_catalog_receivers(catalog, set(event_ids))
    japan_df = filter_japan_receivers(receivers_df)

    receiver_dicts = [
        {
            "event_id": row["event_id"],
            "year": float(row["year"]),
            "lat": float(row["lat"]),
            "lon": float(row["lon"]),
            "magnitude": float(row["magnitude"]),
            "from_s170": bool(row["from_s170"]),
        }
        for _, row in japan_df.iterrows()
    ]

    results = batch_dynamic_stress(receiver_dicts)
    df = pd.DataFrame(results)

    # Distance filter after computing (exact haversine)
    df = df[(df["distance_km"] >= DIST_MIN_KM) & (df["distance_km"] <= DIST_MAX_KM)]
    results = df.to_dict(orient="records")

    logger.info("Japan receivers in distance window: %d", len(df))

    rb = default_rayleigh_band()
    lb = default_love_band()
    summary = _summary_stats(df)

    analysis = {
        "series_id": "S170",
        "source_event": "Sumatra 2004 M9.1",
        "source_parameters": {
            "lat": SUMATRA_2004_LAT,
            "lon": SUMATRA_2004_LON,
            "magnitude": SUMATRA_2004_MW,
        },
        "method": "Brune/Boatwright surface-wave PGV + Hill (1993) σ_dyn = μ·PGV/β",
        "material": {"shear_modulus_gpa": 30.0, "shear_velocity_km_s": 3.5},
        "wave_bands": {
            "Rayleigh": {
                "frequency_hz": rb.frequency_hz,
                "group_velocity_km_s": rb.group_velocity_km_s,
                "quality_factor": rb.quality_factor,
            },
            "Love": {
                "frequency_hz": lb.frequency_hz,
                "group_velocity_km_s": lb.group_velocity_km_s,
                "quality_factor": lb.quality_factor,
            },
        },
        "thresholds_mpa": {
            "low": THRESHOLD_SIGMA_LOW_MPA,
            "high": THRESHOLD_SIGMA_HIGH_MPA,
        },
        "receiver_filter": {
            "lat_range": [JAPAN_LAT_MIN, JAPAN_LAT_MAX],
            "lon_range": [JAPAN_LON_MIN, JAPAN_LON_MAX],
            "distance_km_range": [DIST_MIN_KM, DIST_MAX_KM],
        },
        "summary": summary,
        "threshold_exceeded": {
            "any_receiver_exceeds_0_01_mpa": bool(df["exceeds_0_01_mpa"].any()) if len(df) else False,
            "any_receiver_exceeds_0_1_mpa": bool(df["exceeds_0_1_mpa"].any()) if len(df) else False,
        },
        "events": results,
    }

    out_dir = ROOT / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "dynamic_stress_sumatra2004.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    logger.info("Saved %s", json_path)

    fig_path = ROOT / "figures" / "grl" / "fig08_dynamic_stress_japan.png"
    if len(df):
        plot_dynamic_stress(df, analysis, fig_path)
    else:
        logger.warning("No receivers in distance window — figure skipped")

    logger.info(
        "Summary: median PGV=%.4f cm/s, median σ_dyn=%.5f MPa, "
        "exceeds 0.01 MPa: %s",
        summary["median_pgv_max_cm_s"] or 0,
        summary["median_sigma_dyn_max_mpa"] or 0,
        analysis["threshold_exceeded"]["any_receiver_exceeds_0_01_mpa"],
    )


if __name__ == "__main__":
    main()
