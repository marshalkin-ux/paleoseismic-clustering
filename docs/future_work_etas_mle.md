# Future work: publication-grade ETAS MLE

## Current state (primary null)

**Primary null for hypothesis testing** is **temporal Ogata (1988) MLE** on GK mainshocks
(`scripts/calibrate_etas_mle.py` → `results/etas_mle_calibration.json`):

- **μ, K, α, c, p** fit via L-BFGS-B on 2017 GK mainshocks (1973–2026, M≥6.5)
- Bootstrap 95% CIs (n = 50 resamples)
- **In-sample validation:** `scripts/run_etas_validation.py` → `results/etas_validation.json` (mean = 27.0, **p_ETAS = 1.0**, N_obs = 27)
- **Partial hold-out:** `scripts/calibrate_etas_holdout.py` → `results/etas_holdout_validation.json` (train 1973–2000, validate 2001–2026: N_obs = 13, p = 1.0)

**Limitation:** no spatial kernel; in-sample calibration uses the same detector as validation; ETAS triggering model vs GK-declustered mainshocks — acknowledged mismatch.

## Negative controls (not primary)

### WLS minimal calibration (`scripts/calibrate_etas.py`)

- **Appendix B only** — detector–calibration coupling illustration.

### Literature H&S 2003

Comparison only (`scripts/run_etas_validation_literature.py`).

## Future work (not implemented in current session)

- **Full spatial Ogata (1998) MLE** with long-range kernel — publication-grade spatiotemporal null (R `etas` package or equivalent).
- **Train/test ETAS extensions:** rolling hold-out, pre-1973 exclusion, detector frozen before calibration.
- **Synthetic benchmark:** Bird (2003) plate-boundary geometry or injected global chains with known ground truth.
- **Window-level FDR:** Benjamini–Hochberg on 142 correlated sliding-window tests requires effective-M correction (Gao et al., 2008) — not a discovery procedure as implemented.
- **FDR on merged series:** post-hoc BH on 47 candidates (`results/fdr_correction_results.csv`, `results/fdr_windows.json`) — exploratory only.

## References

- Ogata Y. (1998). Space-time point-process models for earthquake occurrences. *Ann. Inst. Stat. Math.*, 50, 379–402.
- Ogata Y. (1988). Statistical models for earthquake occurrences and residual analysis. *J. Amer. Stat. Assoc.*, 83, 9–27.
- Helmstetter A., Sornette D. (2003). Borehole measurements and the scaling of earthquake triggering. *J. Geophys. Res.*, 108, 2477.
