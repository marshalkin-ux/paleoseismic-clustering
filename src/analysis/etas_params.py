"""Load ETAS parameters: catalog-calibrated MLE (primary) vs WLS/literature (controls)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WLS_CALIBRATION_PATH = ROOT / "results" / "etas_calibration.json"
MLE_CALIBRATION_PATH = ROOT / "results" / "etas_mle_calibration.json"
B0911_CALIBRATION_PATH = ROOT / "results" / "etas_calibration_b0911.json"

# Literature defaults (Helmstetter & Sornette 2003) — comparison only, not primary null
LITERATURE_ETAS = {
    "mu": 0.008,
    "K": 0.08,
    "alpha": 1.0,
    "c": 0.005,
    "p": 1.1,
    "max_trigger_distance_km": 500.0,
    "source": "Helmstetter & Sornette (2003) — literature comparison only",
}


def load_mle_etas_params(
    calibration_path: Path | None = None,
) -> dict[str, float]:
    """Return primary ETAS null: temporal Ogata (1988) MLE on GK mainshocks.

    Fits from ``scripts/calibrate_etas_mle.py`` on 2017 GK mainshocks (1973–2026,
    M≥6.5). Temporal-only MLE (no spatial kernel); see ``docs/future_work_etas_mle.md``.
    """
    path = calibration_path or MLE_CALIBRATION_PATH
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        params = dict(data["parameters_mle"])
        params["_calibration_status"] = data.get("calibration_status", "")
        params["_source"] = data.get("source", str(path))
        if "confidence_intervals_95_bootstrap" in data:
            params["_bootstrap_ci"] = data["confidence_intervals_95_bootstrap"]
        return params
    fallback = dict(LITERATURE_ETAS)
    fallback["_calibration_status"] = "missing_mle_calibration_json"
    fallback["_source"] = "literature fallback (run scripts/calibrate_etas_mle.py)"
    return fallback


def load_calibrated_etas_params(
    calibration_path: Path | None = None,
) -> dict[str, float]:
    """Return catalog-calibrated ETAS params — **primary null** (temporal MLE).

    Alias for ``load_mle_etas_params``; kept for backward compatibility.
    """
    return load_mle_etas_params(calibration_path)


def load_wls_etas_params(
    calibration_path: Path | None = None,
) -> dict[str, float]:
    """Return WLS minimal calibration — **negative control only** (Appendix B).

    Invalid for inference (24 aftershock delays; detector–calibration coupling).
    """
    path = calibration_path or WLS_CALIBRATION_PATH
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        params = dict(data["parameters_calibrated"])
        params["_calibration_status"] = data.get("calibration_status", "")
        params["_source"] = data.get("source", str(path))
        return params
    return load_mle_etas_params()


def load_b0911_etas_params(
    calibration_path: Path | None = None,
) -> dict[str, float]:
    """Return ETAS params with alpha fixed to catalog b=0.911 (sensitivity run)."""
    path = calibration_path or B0911_CALIBRATION_PATH
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        params = dict(data["parameters_calibrated"])
        params["_calibration_status"] = data.get("calibration_status", "")
        params["_source"] = data.get("source", str(path))
        return params
    params = load_wls_etas_params()
    params["alpha"] = 0.911
    params["b_value"] = 0.911
    params["_calibration_status"] = "alpha_fixed_b0911_fallback"
    return params


def load_literature_etas_params() -> dict[str, float]:
    """Return literature ETAS defaults — comparison benchmark only."""
    return dict(LITERATURE_ETAS)
