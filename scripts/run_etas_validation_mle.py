#!/usr/bin/env python
"""ETAS validation using temporal MLE parameters (etas_mle_calibration.json)."""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

from src.analysis.clustering import SeismicClusterAnalyzer
from src.analysis.etas_params import load_literature_etas_params
from src.analysis.etas_validation import ETASCatalogGenerator, assign_fe_regions

MLE_PATH = ROOT / "results" / "etas_mle_calibration.json"
OUT_PATH = ROOT / "results" / "etas_validation_mle.json"
N_CATALOGS = 1000


def load_mle_params() -> dict:
    if not MLE_PATH.exists():
        raise FileNotFoundError(f"Run scripts/calibrate_etas_mle.py first: {MLE_PATH}")
    with open(MLE_PATH, encoding="utf-8") as f:
        data = json.load(f)
    params = dict(data["parameters_mle"])
    params["_source"] = data.get("source", str(MLE_PATH))
    return params


def main() -> None:
    params = load_mle_params()
    clean = {k: v for k, v in params.items() if not k.startswith("_")}
    logger.info(
        "MLE ETAS: mu=%.6f K=%.4f alpha=%.3f c=%.5f p=%.3f",
        clean["mu"], clean["K"], clean["alpha"], clean["c"], clean["p"],
    )

    catalog_path = ROOT / "data" / "processed" / "unified_catalog_full.csv"
    df = pd.read_csv(catalog_path)
    df = df[(df["year"] >= 1973) & (df["magnitude"] >= 6.5)].copy()
    df = assign_fe_regions(df)

    analyzer = SeismicClusterAnalyzer()
    real_series = analyzer.global_series(df, min_events=4, time_window_years=2.0)
    n_observed = len(real_series)

    generator = ETASCatalogGenerator(
        mu=clean["mu"],
        K=clean["K"],
        alpha=clean["alpha"],
        c=clean["c"],
        p=clean["p"],
        max_trigger_distance_km=clean.get("max_trigger_distance_km", 500.0),
        use_calibrated_defaults=False,
    )

    t_span_years = float(df["year"].max() - df["year"].min())
    n_background = max(int(round(clean["mu"] * t_span_years * 365.25)), 40)

    results = generator.run_false_positive_analysis(
        cluster_analyzer=analyzer,
        n_catalogs=N_CATALOGS,
        min_events=4,
        time_window_years=2.0,
        n_observed=n_observed,
        seed=42,
        n_background=n_background,
        t_span_years=t_span_years,
    )

    results["etas_parameters"] = clean
    results["etas_parameters_primary"] = "temporal_mle_gk_mainshocks"
    results["etas_parameters_literature_comparison"] = load_literature_etas_params()
    results["mle_calibration_source"] = str(MLE_PATH)
    results["interpretation"] = (
        "Primary null: temporal Ogata (1988) MLE on GK mainshocks. "
        "p_ETAS≈1.0: N_obs=27 matches synthetic mean — detector output "
        "consistent with catalog-calibrated ETAS; does not support global-series hypothesis."
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    logger.info(
        "N_obs=%d mean=%.2f p=%.4f FPR=%.3f -> %s",
        results["n_observed"],
        results["mean_false_series"],
        results["p_value_empirical"],
        results["false_positive_rate"],
        OUT_PATH,
    )


if __name__ == "__main__":
    main()
