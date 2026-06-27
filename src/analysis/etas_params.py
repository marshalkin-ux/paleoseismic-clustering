"""Load ETAS parameters: catalog-calibrated (primary) vs literature (comparison only)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CALIBRATION_PATH = ROOT / "results" / "etas_calibration.json"

# Literature defaults (Helmstetter & Sornette 2003) — comparison only, NOT primary inference
LITERATURE_ETAS = {
    "mu": 0.008,
    "K": 0.08,
    "alpha": 1.0,
    "c": 0.005,
    "p": 1.1,
    "max_trigger_distance_km": 500.0,
    "source": "Helmstetter & Sornette (2003) — literature comparison only",
}


def load_calibrated_etas_params(
    calibration_path: Path | None = None,
) -> dict[str, float]:
    """Return catalog-calibrated ETAS params (primary null model).

    Fits from ``scripts/calibrate_etas.py``: GK declustering on 2041 modern events,
    Omori MLE on aftershock delays, branching regression for K and alpha.
    """
    path = calibration_path or DEFAULT_CALIBRATION_PATH
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        params = dict(data["parameters_calibrated"])
        params["_calibration_status"] = data.get("calibration_status", "")
        params["_source"] = data.get("source", str(path))
        return params
    # Fallback only if calibration JSON missing — run calibrate_etas.py first
    fallback = dict(LITERATURE_ETAS)
    fallback["_calibration_status"] = "missing_calibration_json"
    fallback["_source"] = "literature fallback (run scripts/calibrate_etas.py)"
    return fallback


def load_literature_etas_params() -> dict[str, float]:
    """Return literature ETAS defaults for sensitivity comparison only."""
    return dict(LITERATURE_ETAS)
