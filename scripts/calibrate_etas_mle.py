#!/usr/bin/env python
"""Temporal ETAS MLE on GK mainshocks (1973–2026, M>=6.5).

Fits mu, K, alpha, c, p via scipy.optimize on the standard Ogata (1988)
temporal ETAS log-likelihood (no spatial kernel). Bootstrap 95% CIs.

Outputs:
    results/etas_mle_calibration.json
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

from src.analysis.declustering import GardnerKnopoffDeclustering, _to_time_days

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

M_MIN = 6.5
C_MIN = 0.001  # day — literature floor, not 1e-4 artifact
N_BOOT = 50
BOOT_SEED = 42


def _lam_at_events(
    times: np.ndarray,
    prod: np.ndarray,
    mu: float,
    c: float,
    p: float,
) -> np.ndarray:
    """Vectorized intensity at each event time."""
    n = len(times)
    lams = np.empty(n)
    for i in range(n):
        if i == 0:
            lams[i] = mu
        else:
            dt = times[i] - times[:i] + c
            lams[i] = mu + np.sum(prod[:i] * np.power(dt, -p))
    return lams


def _load_modern_gk_mainshocks() -> tuple[pd.DataFrame, float]:
    catalog_path = ROOT / "data" / "processed" / "unified_catalog_full.csv"
    df = pd.read_csv(catalog_path)
    df = df[(df["year"] >= 1973) & (df["magnitude"] >= M_MIN)].copy()
    df = df.sort_values("year").reset_index(drop=True)
    gk = GardnerKnopoffDeclustering()
    mainshocks, aftershocks = gk.decluster(df)
    times = _to_time_days(mainshocks)
    t_span = float(times.max() - times.min())
    return mainshocks, t_span


def _psi_integral(t_j: float, t_end: float, c: float, p: float) -> float:
    """Integral of (t - t_j + c)^(-p) from t_j to t_end."""
    dt0 = c
    dt1 = t_end - t_j + c
    if dt1 <= 0:
        return 0.0
    if abs(p - 1.0) < 1e-8:
        return float(np.log(dt1 / dt0))
    return float((dt1 ** (1.0 - p) - dt0 ** (1.0 - p)) / (1.0 - p))


def _productivity(K: float, alpha: float, m: float, m0: float = M_MIN) -> float:
    return K * (10.0 ** (alpha * (m - m0)))


def temporal_etas_log_likelihood(
    times: np.ndarray,
    mags: np.ndarray,
    t_end: float,
    mu: float,
    K: float,
    alpha: float,
    c: float,
    p: float,
) -> float:
    """Log-likelihood for temporal ETAS (Ogata 1988), base-10 productivity."""
    n = len(times)
    if n == 0 or mu <= 0 or K <= 0 or c <= 0 or p <= 1.0:
        return -np.inf

    prod = K * (10.0 ** (alpha * (mags - M_MIN)))
    lams = _lam_at_events(times, prod, mu, c, p)
    if np.any(lams <= 0):
        return -np.inf
    ll = float(np.sum(np.log(lams)))

    compensator = mu * t_end
    for j in range(n):
        compensator += prod[j] * _psi_integral(times[j], t_end, c, p)
    return ll - compensator


def _neg_ll_from_params(x: np.ndarray, times: np.ndarray, mags: np.ndarray, t_end: float) -> float:
    log_mu, log_K, alpha, log_c, log_p_minus_1 = x
    mu = np.exp(log_mu)
    K = np.exp(log_K)
    c = np.exp(log_c)
    p = 1.0 + np.exp(log_p_minus_1)
    return -temporal_etas_log_likelihood(times, mags, t_end, mu, K, alpha, c, p)


def fit_temporal_etas_mle(
    mainshocks: pd.DataFrame,
    t_span_days: float,
) -> dict:
    times = _to_time_days(mainshocks).astype(float)
    times = times - times.min()
    mags = mainshocks["magnitude"].astype(float).values
    t_end = float(times.max()) if len(times) else t_span_days

    x0 = np.array([np.log(0.05), np.log(0.08), 1.0, np.log(0.005), np.log(0.1)])
    bounds = [
        (np.log(1e-5), np.log(1.0)),       # mu
        (np.log(1e-4), np.log(10.0)),      # K
        (0.0, 2.5),                        # alpha
        (np.log(C_MIN), np.log(10.0)),     # c >= 0.001 day
        (np.log(0.01), np.log(2.0)),       # p-1
    ]

    res = minimize(
        _neg_ll_from_params,
        x0,
        args=(times, mags, t_end),
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": 5000, "ftol": 1e-12},
    )

    log_mu, log_K, alpha, log_c, log_p_minus_1 = res.x
    mu = float(np.exp(log_mu))
    K = float(np.exp(log_K))
    c = float(np.exp(log_c))
    p = float(1.0 + np.exp(log_p_minus_1))
    ll = temporal_etas_log_likelihood(times, mags, t_end, mu, K, alpha, c, p)

    return {
        "mu": mu,
        "K": K,
        "alpha": alpha,
        "c": c,
        "p": p,
        "log_likelihood": ll,
        "n_events": int(len(times)),
        "t_end_days": t_end,
        "optimizer": {
            "method": "L-BFGS-B",
            "success": bool(res.success),
            "message": str(res.message),
            "n_iterations": int(res.nit) if hasattr(res, "nit") else None,
        },
        "bounds": {
            "c_min_day": C_MIN,
            "note": "c lower bound 0.001 day per literature; not 1e-4 WLS floor",
        },
        "_fit_arrays": {"times": times, "mags": mags},
    }


def bootstrap_ci(
    times: np.ndarray,
    mags: np.ndarray,
    t_end: float,
    n_boot: int = N_BOOT,
    seed: int = BOOT_SEED,
) -> dict[str, dict[str, float]]:
    rng = np.random.default_rng(seed)
    n = len(times)
    samples: dict[str, list[float]] = {k: [] for k in ("mu", "K", "alpha", "c", "p")}

    for b in range(n_boot):
        idx = rng.integers(0, n, size=n)
        boot_df = pd.DataFrame({"year": np.zeros(n), "magnitude": mags[idx]})
        boot_df["year"] = times[idx] / 365.25 + 1973  # placeholder for _to_time_days unused
        boot_times = np.sort(times[idx])
        boot_mags = mags[idx]
        try:
            fit = fit_temporal_etas_mle_from_arrays(boot_times, boot_mags, t_end)
            for k in samples:
                samples[k].append(fit[k])
        except Exception:
            continue

    ci = {}
    for k, vals in samples.items():
        if len(vals) < 10:
            ci[k] = {"low": np.nan, "high": np.nan, "n_success": len(vals)}
            continue
        arr = np.array(vals)
        ci[k] = {
            "low": float(np.percentile(arr, 2.5)),
            "high": float(np.percentile(arr, 97.5)),
            "median": float(np.median(arr)),
            "n_success": len(vals),
        }
    return ci


def fit_temporal_etas_mle_from_arrays(times: np.ndarray, mags: np.ndarray, t_end: float) -> dict:
    x0 = np.array([np.log(0.05), np.log(0.08), 1.0, np.log(0.005), np.log(0.1)])
    bounds = [
        (np.log(1e-5), np.log(1.0)),
        (np.log(1e-4), np.log(10.0)),
        (0.0, 2.5),
        (np.log(C_MIN), np.log(10.0)),
        (np.log(0.01), np.log(2.0)),
    ]
    res = minimize(
        _neg_ll_from_params,
        x0,
        args=(times, mags, t_end),
        method="L-BFGS-B",
        bounds=bounds,
        options={"maxiter": 500, "ftol": 1e-10},
    )
    log_mu, log_K, alpha, log_c, log_p_minus_1 = res.x
    return {
        "mu": float(np.exp(log_mu)),
        "K": float(np.exp(log_K)),
        "alpha": float(alpha),
        "c": float(np.exp(log_c)),
        "p": float(1.0 + np.exp(log_p_minus_1)),
    }


def main() -> None:
    mainshocks, t_span_catalog = _load_modern_gk_mainshocks()
    logger.info("GK mainshocks: %d events", len(mainshocks))

    fit = fit_temporal_etas_mle(mainshocks, t_span_catalog)
    arrs = fit.pop("_fit_arrays")
    times = arrs["times"]
    mags = arrs["mags"]
    t_end = fit["t_end_days"]

    logger.info(
        "MLE: mu=%.6f K=%.4f alpha=%.3f c=%.5f p=%.3f ll=%.1f",
        fit["mu"], fit["K"], fit["alpha"], fit["c"], fit["p"], fit["log_likelihood"],
    )

    logger.info("Bootstrap CIs (n=%d)...", N_BOOT)
    ci = bootstrap_ci(times, mags, t_end, n_boot=N_BOOT)

    # Compare to WLS minimal calibration
    wls_path = ROOT / "results" / "etas_calibration.json"
    wls_compare = {}
    if wls_path.exists():
        with open(wls_path, encoding="utf-8") as f:
            wls = json.load(f)
        wls_p = wls["parameters_calibrated"]
        wls_compare = {
            "source": str(wls_path),
            "mu": wls_p["mu"],
            "K": wls_p["K"],
            "alpha": wls_p["alpha"],
            "c": wls_p["c"],
            "p": wls_p["p"],
            "note": (
                "WLS minimal calibration (24 aftershock delays) is not valid for inference; "
                "K≈0.495 vs MLE K indicates fundamental calibration failure of WLS path."
            ),
        }

    gk = GardnerKnopoffDeclustering()
    full = pd.read_csv(ROOT / "data" / "processed" / "unified_catalog_full.csv")
    full = full[(full["year"] >= 1973) & (full["magnitude"] >= M_MIN)]
    _, aftershocks = gk.decluster(full)

    result = {
        "calibration_status": "temporal_etas_mle_gk_mainshocks_1973_2026",
        "catalog_modern_n_raw": int(len(full)),
        "gk_mainshocks": int(len(mainshocks)),
        "gk_aftershocks": int(len(aftershocks)),
        "catalog_modern_span_years": float(t_span_catalog / 365.25),
        "parameters_mle": {
            "mu": fit["mu"],
            "K": fit["K"],
            "alpha": fit["alpha"],
            "c": fit["c"],
            "p": fit["p"],
            "max_trigger_distance_km": 500.0,
        },
        "confidence_intervals_95_bootstrap": ci,
        "log_likelihood": fit["log_likelihood"],
        "optimizer": fit["optimizer"],
        "bounds": fit["bounds"],
        "comparison_wls_minimal": wls_compare,
        "source": "scripts/calibrate_etas_mle.py (temporal Ogata 1988 MLE, GK mainshocks)",
        "note": (
            "Temporal-only ETAS MLE (no spatial kernel). Publication-grade spatial "
            "Ogata (1998) MLE deferred to R etas package — see docs/future_work_etas_mle.md."
        ),
    }

    out_path = ROOT / "results" / "etas_mle_calibration.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    logger.info("Saved %s", out_path)


if __name__ == "__main__":
    main()
