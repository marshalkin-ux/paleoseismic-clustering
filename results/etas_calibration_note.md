# ETAS parameter calibration audit

**Date:** 2026-06-27  
**Scope:** Parameters used in `scripts/run_etas_validation.py` and `src/analysis/etas_validation.py`

## Summary

| Parameter | Value used | Catalog-calibrated? |
|-----------|------------|-------------------|
| μ (mu) | 0.008 events/day | **No** — hardcoded default |
| K | 0.08 | **No** — hardcoded default |
| α (alpha) | 1.0 | **No** — hardcoded default |
| c | 0.005 days | **No** — Ogata (1988) typical value |
| p | 1.1 | **No** — Ogata (1988) typical value |
| max_trigger_distance_km | 500 | **No** — methodological choice |

## Evidence

1. **`scripts/run_etas_validation.py`** instantiates `ETASCatalogGenerator(mu=0.008, K=0.08, alpha=1.0, ...)` with literal constants — no MLE or grid search on the 2041-event modern catalog.

2. **`config.yaml`** contains clustering and Monte Carlo settings but **no ETAS parameter block**.

3. **`src/analysis/etas_validation.py`** docstring cites Helmstetter & Sornette (2003) global values; comments say "откалиброваны для глобального каталога M≥6.5" but this refers to literature values, not an in-repo fit to our merged catalog.

4. The modern analysis window uses **2041 events** (1973–2026, M≥6.5 after deduplication). ETAS synthetic catalogs use `n_background=80` over 50 years — a separate simulation design, not a direct fit to 2041 events.

## Simple MLE (optional)

`scripts/calibrate_etas.py --fit-mu` runs a **homogeneous Poisson MLE** for background rate μ on catalog event times only. Full spatial ETAS MLE (Ogata 1998) for K, α, c, p is **not implemented** in this repository.

## Recommended wording for the article

> ETAS null-model validation uses **default global parameters** (μ=0.008, K=0.08, α=1.0, c=0.005 d, p=1.1; Helmstetter & Sornette 2003), **not** values re-calibrated on the 2041-event modern catalog. Rejecting the ETAS null therefore tests whether our series exceed a literature-standard local-aftershock model, not a catalog-specific fit.

## Future work

- Full ETAS MLE on 1973+ catalog (e.g. `etas` R package or PyCSEP)
- Multi-seed robustness (`scripts/run_etas_multiseed.py`)
- Sensitivity sweep on μ, K, α
