# ETAS parameter calibration audit

**Date:** 2026-06-27  
**Scope:** Parameters used in `scripts/run_etas_validation.py` and `src/analysis/etas_validation.py`

## Summary

Parameters are now **catalog-calibrated** via `scripts/calibrate_etas.py` on the **2041-event** modern window (1973–2026, M≥6.5) using Gardner–Knopoff declustering, Omori MLE (c, p), and branching regression (K, α). Background rate μ is estimated from GK mainshock count.

Run:

```bash
python scripts/calibrate_etas.py
python scripts/run_etas_validation.py
```

Output: `results/etas_calibration.json`, `results/etas_validation.json`

## Recommended wording for the article

> ETAS null-model validation uses parameters estimated by minimal MLE on the 2,041-event modern catalog (`results/etas_calibration.json`). Rejecting the ETAS null tests whether observed series exceed a catalog-calibrated local-aftershock model without long-range links (>500 km). The series detector remains liberal on ETAS nulls (FPR = 1000/1000); tightening criteria is documented under Limitations.

## Future work

- Full spatial ETAS MLE (Ogata 1998; e.g. PyCSEP)
- Multi-seed robustness (`scripts/run_etas_multiseed.py`)
- Tighter series criteria if FPR remains 100%
