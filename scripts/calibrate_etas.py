#!/usr/bin/env python
"""ETAS parameter calibration stub / simple MLE on catalog event times.

The ETAS validation pipeline (``scripts/run_etas_validation.py``) uses
**hardcoded global defaults** (mu=0.008, K=0.08, alpha=1.0) from
Helmstetter & Sornette (2003), not values fitted to the 2041-event modern
catalog.  This script documents that fact and optionally runs a lightweight
time-domain MLE for background rate mu on the 1973+ catalog.

Full spatial ETAS MLE (Ogata 1998) is deferred; see ``results/etas_calibration_note.md``.

Usage
-----
    python scripts/calibrate_etas.py
    python scripts/calibrate_etas.py --fit-mu

Outputs
-------
    results/etas_calibration.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

# Defaults used in run_etas_validation.py (hardcoded, not catalog-fitted)
DEFAULT_ETAS = {
    "mu": 0.008,
    "K": 0.08,
    "alpha": 1.0,
    "c": 0.005,
    "p": 1.1,
    "max_trigger_distance_km": 500.0,
}


def _poisson_log_likelihood_mu(mu: float, n_events: int, t_days: float) -> float:
    """Homogeneous Poisson log-likelihood for background rate (events/day)."""
    if mu <= 0:
        return -1e30
    return n_events * np.log(mu) - mu * t_days


def estimate_background_mu(events: pd.DataFrame) -> dict:
    """Simple MLE for homogeneous background rate on catalog times."""
    t0 = events["year"].min()
    t1 = events["year"].max()
    t_days = (t1 - t0) * 365.25
    n = len(events)
    # MLE for homogeneous rate
    mu_hat = n / t_days
    res = minimize_scalar(
        lambda m: -_poisson_log_likelihood_mu(m, n, t_days),
        bounds=(1e-6, 1.0),
        method="bounded",
    )
    return {
        "n_events": n,
        "t_span_years": float(t1 - t0),
        "mu_mle_homogeneous": float(mu_hat),
        "mu_mle_optimized": float(res.x),
        "note": "Homogeneous Poisson MLE only; K/alpha not fitted",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="ETAS calibration stub")
    parser.add_argument("--fit-mu", action="store_true", help="Run simple mu MLE on 1973+ catalog")
    args = parser.parse_args()

    catalog_path = ROOT / "data" / "processed" / "unified_catalog_full.csv"
    df = pd.read_csv(catalog_path)
    modern = df[df["year"] >= 1973].copy()

    note = {
        "calibration_status": "hardcoded_global_defaults",
        "source": "Helmstetter & Sornette (2003) via src/analysis/etas_validation.py",
        "parameters_used_in_validation": DEFAULT_ETAS,
        "catalog_modern_n": int(len(modern)),
        "catalog_modern_note": "2041 events after merge in paper; full CSV may differ slightly",
        "config_yaml_etas_section": "none — ETAS params not in config.yaml",
        "recommendation": "Report as default global ETAS parameters, not catalog-calibrated",
    }

    if args.fit_mu:
        note["mu_fit"] = estimate_background_mu(modern)
        logger.info("mu MLE (homogeneous): %.6f events/day", note["mu_fit"]["mu_mle_homogeneous"])

    out_path = ROOT / "results" / "etas_calibration.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(note, f, indent=2, ensure_ascii=False)
    logger.info("Saved %s", out_path)


if __name__ == "__main__":
    main()
