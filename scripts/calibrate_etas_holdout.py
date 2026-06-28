#!/usr/bin/env python
"""Train/test ETAS hold-out validation.

Calibrate temporal Ogata (1988) MLE on GK mainshocks 1973–2000 (train).
Validate N_series on hold-out catalog 2001–2026 with train-calibrated params.

Outputs:
    results/etas_holdout_validation.json
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.calibrate_etas_mle import M_MIN, fit_temporal_etas_mle
from src.analysis.clustering import SeismicClusterAnalyzer
from src.analysis.declustering import GardnerKnopoffDeclustering, _to_time_days
from src.analysis.etas_validation import ETASCatalogGenerator, assign_fe_regions

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

TRAIN_END = 2000
HOLDOUT_START = 2001
N_CATALOGS = 1000
SEED = 42
MAX_TOTAL_EVENTS = 5000
TIME_WINDOW_YEARS = 2.0
MIN_EVENTS = 4


def _gk_mainshocks_in_range(year_min: int, year_max: int) -> tuple[pd.DataFrame, float]:
    catalog_path = ROOT / "data" / "processed" / "unified_catalog_full.csv"
    df = pd.read_csv(catalog_path)
    df = df[(df["year"] >= year_min) & (df["year"] <= year_max) & (df["magnitude"] >= M_MIN)].copy()
    df = df.sort_values("year").reset_index(drop=True)
    gk = GardnerKnopoffDeclustering()
    mainshocks, _ = gk.decluster(df)
    times = _to_time_days(mainshocks)
    t_span = float(times.max() - times.min()) if len(times) else 0.0
    return mainshocks, t_span


def _catalog_holdout() -> pd.DataFrame:
    catalog_path = ROOT / "data" / "processed" / "unified_catalog_full.csv"
    df = pd.read_csv(catalog_path)
    df = df[(df["year"] >= HOLDOUT_START) & (df["magnitude"] >= M_MIN)].copy()
    return assign_fe_regions(df)


def main() -> None:
    train_ms, train_span = _gk_mainshocks_in_range(1973, TRAIN_END)
    logger.info("Train GK mainshocks (%d–%d): %d events", 1973, TRAIN_END, len(train_ms))

    fit = fit_temporal_etas_mle(train_ms, train_span)
    fit.pop("_fit_arrays", None)
    params = {
        "mu": fit["mu"],
        "K": fit["K"],
        "alpha": fit["alpha"],
        "c": fit["c"],
        "p": fit["p"],
        "max_trigger_distance_km": 500.0,
    }
    logger.info(
        "Train MLE: mu=%.6f K=%.4f alpha=%.3f c=%.5f p=%.3f",
        params["mu"], params["K"], params["alpha"], params["c"], params["p"],
    )

    holdout_df = _catalog_holdout()
    t_span_holdout = float(holdout_df["year"].max() - holdout_df["year"].min()) if len(holdout_df) else 0.0
    logger.info("Hold-out catalog (%d+): %d events, span %.1f yr", HOLDOUT_START, len(holdout_df), t_span_holdout)

    analyzer = SeismicClusterAnalyzer()
    holdout_series = analyzer.global_series(
        holdout_df,
        min_events=MIN_EVENTS,
        time_window_years=TIME_WINDOW_YEARS,
    )
    n_observed = len(holdout_series)
    logger.info("Hold-out N_series: %d", n_observed)

    n_background = int(round(params["mu"] * t_span_holdout * 365.25))
    n_background = max(n_background, 20)

    generator = ETASCatalogGenerator(
        mu=params["mu"],
        K=params["K"],
        alpha=params["alpha"],
        c=params["c"],
        p=params["p"],
        max_trigger_distance_km=params["max_trigger_distance_km"],
        use_calibrated_defaults=False,
    )

    logger.info("ETAS synthetics (n=%d, max_total_events=%d)...", N_CATALOGS, MAX_TOTAL_EVENTS)
    validation = generator.run_false_positive_analysis(
        cluster_analyzer=analyzer,
        n_catalogs=N_CATALOGS,
        min_events=MIN_EVENTS,
        time_window_years=TIME_WINDOW_YEARS,
        n_observed=n_observed,
        seed=SEED,
        n_background=n_background,
        t_span_years=t_span_holdout,
        max_total_events=MAX_TOTAL_EVENTS,
    )

    result = {
        "calibration_status": "temporal_etas_mle_holdout_train1973_2000_validate2001_2026",
        "train_period": f"1973-{TRAIN_END}",
        "holdout_period": f"{HOLDOUT_START}-2026",
        "train_gk_mainshocks": int(len(train_ms)),
        "holdout_catalog_n": int(len(holdout_df)),
        "holdout_span_years": t_span_holdout,
        "parameters_train_mle": params,
        "train_optimizer": fit.get("optimizer"),
        "n_observed_holdout": n_observed,
        "n_catalogs": N_CATALOGS,
        "max_total_events": MAX_TOTAL_EVENTS,
        "n_background_per_catalog": n_background,
        "mean_false_series": validation["mean_false_series"],
        "std_false_series": validation["std_false_series"],
        "p_value_empirical": validation["p_value_empirical"],
        "false_positive_rate": validation["false_positive_rate"],
        "max_false_series": validation["max_false_series"],
        "detector": {
            "time_window_years": TIME_WINDOW_YEARS,
            "min_events": MIN_EVENTS,
            "criterion": "mean_pairwise_gc_km > 1500",
        },
        "interpretation": (
            "Out-of-sample temporal ETAS validation: MLE fit on train GK mainshocks only; "
            "hold-out detector run on 2001–2026 catalog. "
            "Complements (does not replace) in-sample p_ETAS=1.0 on full 1973–2026 window."
        ),
        "model_mismatch_note": (
            "ETAS is a triggering model fit on GK-declustered mainshocks; "
            "declustering removes events the model would treat as offspring — acknowledged limitation."
        ),
        "source": "scripts/calibrate_etas_holdout.py",
    }

    out_path = ROOT / "results" / "etas_holdout_validation.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    logger.info(
        "Hold-out: N_obs=%d mean=%.2f p=%.4f → %s",
        n_observed,
        validation["mean_false_series"],
        validation["p_value_empirical"],
        out_path,
    )
    print(f"\n=== ETAS HOLD-OUT VALIDATION ===")
    print(f"Train: 1973–{TRAIN_END} ({len(train_ms)} GK mainshocks)")
    print(f"Hold-out N_series: {n_observed}")
    print(f"Synthetic mean: {validation['mean_false_series']:.2f} ± {validation['std_false_series']:.2f}")
    print(f"p_ETAS (hold-out): {validation['p_value_empirical']:.4f}")


if __name__ == "__main__":
    main()
