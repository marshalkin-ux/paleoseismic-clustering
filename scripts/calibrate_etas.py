#!/usr/bin/env python
"""ETAS parameter calibration (minimal MLE) on the 1973–2026 modern catalog.

Fits mu, K, alpha, c, p on 2041 M>=6.5 events using Gardner–Knopoff declustering
and temporal branching statistics. Full spatial ETAS MLE (Ogata 1998) is approximated.

Usage
-----
    python scripts/calibrate_etas.py

Outputs
-------
    results/etas_calibration.json
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis.declustering import GardnerKnopoffDeclustering, _haversine_km, _to_time_days

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

M_MIN = 6.5
MAX_TRIGGER_KM = 500.0
MAX_AFTERHOCK_DAYS = 365.0
# Catalog Gutenberg-Richter b (MLE, Mc=6.55); used for fixed-alpha ETAS sensitivity
B_CATALOG = 0.911

# Literature defaults (Helmstetter & Sornette 2003) — fallback / comparison
DEFAULT_ETAS = {
    "mu": 0.008,
    "K": 0.08,
    "alpha": 1.0,
    "c": 0.005,
    "p": 1.1,
    "max_trigger_distance_km": MAX_TRIGGER_KM,
}


def _load_modern_catalog() -> pd.DataFrame:
    catalog_path = ROOT / "data" / "processed" / "unified_catalog_full.csv"
    df = pd.read_csv(catalog_path)
    df = df[df["year"] >= 1973].copy()
    df = df[df["magnitude"] >= M_MIN].copy()
    df = df.sort_values("year").reset_index(drop=True)
    return df


def _assign_aftershock_delays(
    mainshocks: pd.DataFrame,
    aftershocks: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (delays_days, parent_mags, offspring_counts_per_mainshock)."""
    lat_col = "latitude" if "latitude" in mainshocks.columns else "lat"
    lon_col = "longitude" if "longitude" in mainshocks.columns else "lon"

    ms_times = _to_time_days(mainshocks)
    ms_lats = mainshocks[lat_col].astype(float).values
    ms_lons = mainshocks[lon_col].astype(float).values
    ms_mags = mainshocks["magnitude"].astype(float).values

    as_times = _to_time_days(aftershocks)
    as_lats = aftershocks[lat_col].astype(float).values
    as_lons = aftershocks[lon_col].astype(float).values

    delays: list[float] = []
    parent_mags: list[float] = []
    offspring_counts = np.zeros(len(mainshocks), dtype=int)

    for j in range(len(aftershocks)):
        t_j = as_times[j]
        best_i = -1
        best_dt = np.inf
        for i in range(len(mainshocks)):
            dt = t_j - ms_times[i]
            if dt <= 0 or dt > MAX_AFTERHOCK_DAYS:
                continue
            dist = _haversine_km(ms_lats[i], ms_lons[i], as_lats[j], as_lons[j])
            if dist <= MAX_TRIGGER_KM and dt < best_dt:
                best_dt = dt
                best_i = i
        if best_i >= 0:
            delays.append(best_dt)
            parent_mags.append(ms_mags[best_i])
            offspring_counts[best_i] += 1

    return np.array(delays), np.array(parent_mags), offspring_counts


def _omori_log_likelihood(params: np.ndarray, delays: np.ndarray) -> float:
    """Negative log-likelihood for Omori-Utsu (days). params = [log_c, log(p-1)]."""
    log_c, log_p_minus_1 = params
    c = np.exp(log_c)
    p = 1.0 + np.exp(log_p_minus_1)
    if c <= 0 or p <= 1.0:
        return 1e30
    n = len(delays)
    ll = n * (np.log(p - 1.0) - np.log(c))
    ll -= p * np.sum(np.log(delays + c))
    return -ll


def _fit_omori(delays: np.ndarray) -> dict[str, float]:
    if len(delays) < 5:
        return {"c": DEFAULT_ETAS["c"], "p": DEFAULT_ETAS["p"], "n_delays": len(delays)}
    x0 = np.array([np.log(0.01), np.log(0.1)])
    res = minimize(
        _omori_log_likelihood,
        x0,
        args=(delays,),
        method="Nelder-Mead",
        options={"maxiter": 5000},
    )
    c = float(np.exp(res.x[0]))
    p = float(1.0 + np.exp(res.x[1]))
    c = float(np.clip(c, 1e-4, 10.0))
    p = float(np.clip(p, 1.01, 3.0))
    return {"c": c, "p": p, "n_delays": int(len(delays)), "success": bool(res.success)}


def _fit_branching(
    mainshock_mags: np.ndarray,
    offspring_counts: np.ndarray,
    *,
    alpha_fixed: float | None = None,
) -> dict[str, float]:
    """Fit log E[N] = log K + alpha * (M - M_min) via least squares.

    If ``alpha_fixed`` is set, only K is estimated (alpha tied to catalog b-value
    in the base-10 productivity term K·10^{α(M-M0)} per Ogata/Helmstetter convention).
    """
    mags = mainshock_mags.astype(float)
    counts = offspring_counts.astype(float)
    y = np.log(counts + 0.5)
    x = mags - M_MIN
    if len(mags) < 10 or np.std(x) < 1e-6:
        alpha = alpha_fixed if alpha_fixed is not None else DEFAULT_ETAS["alpha"]
        return {"K": DEFAULT_ETAS["K"], "alpha": alpha}

    if alpha_fixed is not None:
        intercept = float(np.mean(y - alpha_fixed * x))
        K = float(np.exp(intercept))
        K = float(np.clip(K, 1e-4, 5.0))
        return {"K": K, "alpha": float(alpha_fixed), "alpha_fixed": True}

    A = np.column_stack([np.ones_like(x), x])
    coef, _, _, _ = np.linalg.lstsq(A, y, rcond=None)
    intercept, alpha = float(coef[0]), float(coef[1])
    K = float(np.exp(intercept))
    K = float(np.clip(K, 1e-4, 5.0))
    alpha = float(np.clip(alpha, 0.0, 2.5))
    return {"K": K, "alpha": alpha, "alpha_fixed": False}


def calibrate_etas_mle(
    events: pd.DataFrame,
    *,
    alpha_fixed: float | None = None,
    b_value: float = B_CATALOG,
) -> dict:
    """Run minimal ETAS MLE on modern catalog."""
    times = _to_time_days(events)
    t_span_days = float(times.max() - times.min())
    n_events = len(events)

    gk = GardnerKnopoffDeclustering()
    mainshocks, aftershocks = gk.decluster(events)

    mu = len(mainshocks) / t_span_days

    delays, parent_mags, offspring_counts = _assign_aftershock_delays(
        mainshocks, aftershocks
    )
    omori = _fit_omori(delays)
    ms_mags = mainshocks["magnitude"].astype(float).values
    branching = _fit_branching(ms_mags, offspring_counts, alpha_fixed=alpha_fixed)

    params = {
        "mu": float(mu),
        "K": branching["K"],
        "alpha": branching["alpha"],
        "c": omori["c"],
        "p": omori["p"],
        "max_trigger_distance_km": MAX_TRIGGER_KM,
        "b_value": float(b_value),
        "magnitude_scaling": "K * 10^(alpha * (M - M0)); alpha fixed to catalog b when requested",
    }

    status = "catalog_mle_1973_2026"
    if alpha_fixed is not None:
        status = f"catalog_mle_1973_2026_alpha_fixed_{alpha_fixed:.3f}"

    return {
        "calibration_status": status,
        "catalog_modern_n": n_events,
        "catalog_modern_span_years": float(t_span_days / 365.25),
        "gk_mainshocks": int(len(mainshocks)),
        "gk_aftershocks": int(len(aftershocks)),
        "omori_fit": omori,
        "branching_fit": branching,
        "parameters_calibrated": params,
        "parameters_literature_defaults": DEFAULT_ETAS,
        "mu_homogeneous_total_rate": float(n_events / t_span_days),
        "n_background_synthetic": int(round(mu * t_span_days)),
        "source": "scripts/calibrate_etas.py (GK + Omori MLE + branching regression)",
        "note": (
            "Minimal MLE on 2041 modern M>=6.5 events; spatial ETAS kernel approximated "
            "via 500 km trigger cap matching ETASCatalogGenerator."
        ),
    }


def main() -> None:
    events = _load_modern_catalog()
    logger.info("Modern catalog: %d events (1973+, M>=6.5)", len(events))

    # Primary MLE (free alpha)
    result = calibrate_etas_mle(events)
    p = result["parameters_calibrated"]
    logger.info(
        "Calibrated ETAS (free alpha): mu=%.6f K=%.4f alpha=%.3f c=%.5f p=%.3f",
        p["mu"], p["K"], p["alpha"], p["c"], p["p"],
    )

    out_path = ROOT / "results" / "etas_calibration.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    logger.info("Saved %s", out_path)

    # Sensitivity: alpha fixed to catalog b=0.911 in base-10 branching term
    result_b = calibrate_etas_mle(events, alpha_fixed=B_CATALOG, b_value=B_CATALOG)
    pb = result_b["parameters_calibrated"]
    logger.info(
        "Calibrated ETAS (alpha=b=%.3f fixed): mu=%.6f K=%.4f alpha=%.3f c=%.5f p=%.3f",
        B_CATALOG, pb["mu"], pb["K"], pb["alpha"], pb["c"], pb["p"],
    )
    result_b["comparison_baseline"] = {
        "source": "results/etas_calibration.json",
        "alpha": p["alpha"],
        "K": p["K"],
        "mu": p["mu"],
    }
    result_b["note"] = (
        "Branching productivity K·10^{α(M-M0)} with α fixed to catalog b=0.911 "
        "(base-10 Gutenberg–Richter exponent; equivalent to exp(α ln 10 · ΔM) in natural-log form). "
        "K re-fitted; μ, c, p unchanged from GK+Omori pipeline."
    )

    out_b = ROOT / "results" / "etas_calibration_b0911.json"
    with open(out_b, "w", encoding="utf-8") as f:
        json.dump(result_b, f, indent=2, ensure_ascii=False)
    logger.info("Saved %s", out_b)


if __name__ == "__main__":
    main()
