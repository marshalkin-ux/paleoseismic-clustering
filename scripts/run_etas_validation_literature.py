#!/usr/bin/env python
"""ETAS validation with literature H&S 2003 parameters (comparison only).

Primary null is catalog-calibrated temporal MLE (run_etas_validation.py).
This script reproduces the literature benchmark cited for sensitivity.

Outputs:
    results/etas_validation_literature.json
"""

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

OUT_PATH = ROOT / "results" / "etas_validation_literature.json"
N_CATALOGS = 1000


def main() -> None:
    params = load_literature_etas_params()
    clean = {k: v for k, v in params.items() if not k.startswith("_")}
    logger.info(
        "Literature ETAS: mu=%.6f K=%.4f alpha=%.3f c=%.5f p=%.3f",
        clean["mu"], clean["K"], clean["alpha"], clean["c"], clean["p"],
    )

    catalog_path = ROOT / "data" / "processed" / "unified_catalog_full.csv"
    df = pd.read_csv(catalog_path)
    df = df[(df["year"] >= 1973) & (df["magnitude"] >= 6.5)].copy()
    df = assign_fe_regions(df)

    analyzer = SeismicClusterAnalyzer()
    real_series = analyzer.global_series(df, min_events=4, time_window_years=2.0)
    n_observed = len(real_series)

    t_span_years = float(df["year"].max() - df["year"].min())
    n_background = max(int(round(clean["mu"] * t_span_years * 365.25)), 40)

    generator = ETASCatalogGenerator(
        mu=clean["mu"],
        K=clean["K"],
        alpha=clean["alpha"],
        c=clean["c"],
        p=clean["p"],
        max_trigger_distance_km=clean.get("max_trigger_distance_km", 500.0),
        use_calibrated_defaults=False,
    )

    results = generator.run_false_positive_analysis(
        cluster_analyzer=analyzer,
        n_catalogs=N_CATALOGS,
        min_events=4,
        time_window_years=2.0,
        n_observed=n_observed,
        seed=42,
        n_background=n_background,
        t_span_years=t_span_years,
        max_total_events=5000,
    )

    results["etas_parameters"] = clean
    results["etas_parameters_role"] = "literature_comparison_only"
    results["note"] = (
        "Helmstetter & Sornette (2003) plug-in values — invalid as primary null "
        "for this catalog; retained for literature benchmark comparison only."
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    logger.info(
        "N_obs=%d mean=%.2f p=%.4f -> %s",
        results["n_observed"],
        results["mean_false_series"],
        results["p_value_empirical"],
        OUT_PATH,
    )


if __name__ == "__main__":
    main()
