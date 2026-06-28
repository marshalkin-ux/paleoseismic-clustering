# Future work: publication-grade ETAS MLE

## Current state (primary null)

**Primary null for hypothesis testing** is **temporal Ogata (1988) MLE** on GK mainshocks
(`scripts/calibrate_etas_mle.py` → `results/etas_mle_calibration.json`):

- **μ, K, α, c, p** fit via L-BFGS-B on 2017 GK mainshocks (1973–2026, M≥6.5)
- Bootstrap 95% CIs (n = 50 resamples)
- Validation: `scripts/run_etas_validation.py` → `results/etas_validation.json`
- **Result:** mean false series = 27.0, **p_ETAS = 1.0** (N_obs = 27)

**Limitation:** no spatial kernel — publication-grade calibration requires spatial Ogata (1998) MLE.

## Negative controls (not primary)

### WLS minimal calibration (`scripts/calibrate_etas.py`)

- **μ** — closed-form GK-mainshock rate
- **c, p** — Nelder–Mead on 24 GK aftershock delays (≤500 km)
- **K, α** — weighted least squares on the same 24 events

**Invalid for inference.** Yields **p_ETAS = 1.0** when mean false series equals **N_obs = 27** —
illustrates detector–calibration coupling. **Appendix B only.**

### Literature H&S 2003

Plug-in values (μ = 0.008, K = 0.08) were **wrongly used as primary null** in earlier drafts.
`scripts/run_etas_validation_literature.py` → `results/etas_validation_literature.json` for comparison.

## Target: Ogata (1998) spatial ETAS MLE

Publication-grade ETAS calibration requires:

1. **Full spatial–temporal likelihood** (Ogata 1998) with background rate μ(x,y,t) or regional partitioning
2. **Maximum likelihood** with profile likelihood or bootstrap **confidence intervals** for K, α, c, p
3. **Decoupling** from the global-series detector — parameters estimated on declustered mainshocks

### Recommended toolchain (R)

```r
library(etas)
# Export GK mainshocks → etasfit() with fixed M0 = 6.5
# Compare to results/etas_mle_calibration.json
```

See `scripts/calibrate_etas_mle.py` for the implemented temporal-only path.

## References

- Ogata Y. (1998). Space-time point-process models for earthquake occurrences. *Ann. Inst. Stat. Math.*, 50, 379–402.
- Ogata Y. (1988). Statistical models for earthquake occurrences and residual analysis. *J. Amer. Stat. Assoc.*, 83, 9–27.
- Helmstetter A., Sornette D. (2003). Borehole measurements and the scaling of earthquake triggering. *J. Geophys. Res.*, 108, 2477.
