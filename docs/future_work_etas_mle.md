# Future work: publication-grade ETAS MLE

## Current state

The repository uses a **minimal WLS calibration** (`scripts/calibrate_etas.py`):

- **μ** — closed-form GK-mainshock rate
- **c, p** — Nelder–Mead on 24 GK aftershock delays (≤500 km)
- **K, α** — weighted least squares (WLS) on the same 24 events

This is **invalid for inference**. Catalog-matched WLS yields **p_ETAS = 1.0** when mean false series equals **N_obs = 27** — a **negative control** illustrating detector–calibration coupling when **K** is fit on the same catalog used to count candidates. **K ≈ 0.495 vs literature ~0.08 indicates fundamental calibration failure**, not mere simplification. **Do not cite p_ETAS = 1.0 as independent falsification evidence.**

**Primary null for hypothesis testing** remains literature Helmstetter & Sornette (2003) parameters (μ = 0.008, K = 0.08), decoupled from detector output.

## Attempted: temporal ETAS MLE (Python)

`scripts/calibrate_etas_mle.py` fits **μ, K, α, c, p** on GK mainshocks via `scipy.optimize` (L-BFGS-B) on the standard **temporal** Ogata (1988) log-likelihood:

- **c lower bound: 0.001 day** (literature floor; not the 10⁻⁴ WLS artifact)
- Bootstrap 95% CIs (n = 200 resamples)
- Output: `results/etas_mle_calibration.json`
- Validation: `scripts/run_etas_validation_mle.py` → `results/etas_validation_mle.json`

**Limitation:** no spatial kernel — publication-grade calibration requires spatial Ogata (1998) MLE.

## Target: Ogata (1998) spatial ETAS MLE

Publication-grade ETAS calibration requires:

1. **Full spatial–temporal likelihood** (Ogata 1998) with background rate μ(x,y,t) or regional partitioning
2. **Maximum likelihood** with profile likelihood or bootstrap **confidence intervals** for K, α, c, p
3. **Decoupling** from the global-series detector — parameters estimated on declustered mainshocks, validated on held-out windows or independent regional catalogs

### Recommended toolchain (R)

```r
# Install
install.packages("etas")

# Workflow (sketch)
library(etas)
# 1. Export GK mainshocks: data/export/gk_mainshocks_1973_2026.csv
#    columns: date_time (UTC), lat, lon, mag
# 2. Convert to etas input object (see package vignette)
# 3. etas() or etasfit() with fixed M0 = 6.5
# 4. Compare K, alpha, c, p to results/etas_mle_calibration.json and WLS values
# 5. Profile/bootstrap CIs from fitted object
# 6. Export parameters to JSON for run_etas_validation.py
```

Concrete steps:

1. Export GK-mainshock catalog (2017 events, 1973–2026) to CSV with UTC time, lat, lon, M (`scripts/export_gk_mainshocks.py` — to be added)
2. Fit spatial ETAS MLE in R [`etas`](https://cran.r-project.org/package=etas) with fixed M₀ = 6.5
3. Regenerate 1000 synthetic catalogs with MLE parameters + 500 km cutoff; recompute p_ETAS
4. Report parameter CIs; if p_ETAS remains ≈ 1.0 under spatial MLE, interpret as detector liberalism, not calibration artifact

### Python alternative

Full spatial reimplementation using `scipy.optimize` on Ogata (1998) likelihood with spatial kernel — estimated effort >4 h; temporal-only path implemented in `calibrate_etas_mle.py`.

## References

- Ogata Y. (1998). Space-time point-process models for earthquake occurrences. *Ann. Inst. Stat. Math.*, 50, 379–402.
- Ogata Y. (1988). Statistical models for earthquake occurrences and residual analysis. *J. Amer. Stat. Assoc.*, 83, 9–27.
- Helmstetter A., Sornette D. (2003). Borehole measurements and the scaling of earthquake triggering. *J. Geophys. Res.*, 108, 2477.
