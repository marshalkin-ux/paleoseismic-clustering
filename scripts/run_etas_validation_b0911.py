#!/usr/bin/env python
"""ETAS validation with alpha fixed to catalog b=0.911 in branching term.

Outputs:
    results/etas_validation_b0911.json
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

from src.analysis.etas_params import load_b0911_etas_params, load_calibrated_etas_params
from src.analysis.etas_validation import ETASCatalogGenerator, assign_fe_regions
from src.analysis.clustering import SeismicClusterAnalyzer

BASELINE_PATH = ROOT / "results" / "etas_validation.json"
OUT_PATH = ROOT / "results" / "etas_validation_b0911.json"
N_CATALOGS = 50


def main() -> None:
    catalog_path = ROOT / "data" / "processed" / "unified_catalog_full.csv"
    df = pd.read_csv(catalog_path)
    df = df[(df["year"] >= 1973) & (df["magnitude"] >= 6.5)].copy()
    df = assign_fe_regions(df)

    etas_params = load_b0911_etas_params()
    clean = {k: v for k, v in etas_params.items() if not k.startswith("_")}
    logger.info(
        "ETAS b=0.911: mu=%.6f K=%.4f alpha=%.3f c=%.5f p=%.3f b=%.3f",
        clean["mu"], clean["K"], clean["alpha"], clean["c"], clean["p"],
        clean.get("b_value", 0.911),
    )

    analyzer = SeismicClusterAnalyzer()
    real_series = analyzer.global_series(df, min_events=4, time_window_years=2.0)
    n_observed = len(real_series)
    logger.info("Observed global series (GC>1500 km): %d", n_observed)

    t_span_years = float(df["year"].max() - df["year"].min())
    n_background = max(int(round(clean["mu"] * t_span_years * 365.25)), 40)

    generator = ETASCatalogGenerator(
        mu=clean["mu"],
        K=clean["K"],
        alpha=clean["alpha"],
        c=clean["c"],
        p=clean["p"],
        b=float(clean.get("b_value", 0.911)),
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
        max_total_events=3000,
    )

    baseline = {}
    if BASELINE_PATH.exists():
        with open(BASELINE_PATH, encoding="utf-8") as f:
            baseline = json.load(f)

    primary = load_calibrated_etas_params()
    results["etas_parameters"] = clean
    results["etas_parameters_primary"] = "catalog_mle_alpha_fixed_b0911"
    results["alpha_convention"] = (
        "K * 10^(alpha * (M - M0)) with alpha = catalog b = 0.911; "
        "equivalent Ogata natural-log exponent alpha_nat = b * ln(10) ≈ 2.097"
    )
    results["comparison_free_alpha"] = {
        "source": "results/etas_calibration.json",
        "alpha": primary.get("alpha"),
        "K": primary.get("K"),
        "p_ETAS": baseline.get("p_value_empirical"),
        "mean_false_series": baseline.get("mean_false_series"),
        "false_positive_rate": baseline.get("false_positive_rate"),
        "n_observed_baseline": baseline.get("n_observed"),
    }
    results["n_background_per_catalog"] = n_background
    results["catalog_span_years"] = t_span_years
    results["max_total_events_per_catalog"] = 3000
    results["note_max_events"] = (
        "alpha=b=0.911 increases branching; catalogs capped at 3000 events "
        "for validation runtime (comparable to ~2041 modern events)."
    )
    results["clustering_criterion"] = "mean_pairwise_gc_km > 1500"

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n=== ETAS VALIDATION (alpha = b = 0.911) ===")
    print(f"N_observed:           {results['n_observed']}")
    print(f"Mean false series:    {results['mean_false_series']:.2f}")
    print(f"FPR:                  {results['false_positive_rate']:.3f}")
    print(f"p_ETAS:               {results['p_value_empirical']:.4f}")
    if baseline:
        print(f"p_ETAS (free alpha):  {baseline.get('p_value_empirical')}")
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()
