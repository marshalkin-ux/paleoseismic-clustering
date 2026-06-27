# Future work: publication-grade ETAS MLE

## Current state

The repository uses a **minimal calibration** (`scripts/calibrate_etas.py`):

- **μ** — closed-form GK-mainshock rate
- **c, p** — Nelder–Mead on 24 GK aftershock delays (≤500 km)
- **K, α** — weighted least squares (WLS) on the same 24 events

This is **exploratory only**. Catalog-matched WLS yields **p_ETAS = 1.0** when mean false series equals **N_obs = 27** — a **negative control** illustrating detector–calibration coupling when **K** is fit on the same catalog used to count candidates. **Do not cite p_ETAS = 1.0 as independent falsification evidence.**

**Primary null for hypothesis testing** remains literature Helmstetter & Sornette (2003) parameters (μ = 0.008, K = 0.08), decoupled from detector output.

## Target: Ogata (1998) spatial ETAS MLE

Publication-grade ETAS calibration requires:

1. **Full spatial–temporal likelihood** (Ogata 1998) with background rate μ(x,y,t) or regional partitioning
2. **Maximum likelihood** with profile likelihood or bootstrap **confidence intervals** for K, α, c, p
3. **Decoupling** from the global-series detector — parameters estimated on declustered mainshocks, validated on held-out windows or independent regional catalogs

### Recommended toolchain

- **R** [`etas`](https://cran.r-project.org/package=etas) package (Ogata-style MLE, documented in JMA / statistical seismology workflows)
- Alternative: Python reimplementation using `scipy.optimize` on the standard ETAS log-likelihood with spatial kernel (estimated effort >2 h; not yet implemented)

### Concrete plan

1. Export GK-mainshock catalog (2017 events, 1973–2026) to CSV with UTC time, lat, lon, M
2. Fit spatial ETAS MLE in R `etas` with fixed M₀ = 6.5, compare K, α, c, p to current WLS values
3. Regenerate 1000 synthetic catalogs with MLE parameters + 500 km cutoff; recompute p_ETAS
4. Report parameter CIs; if p_ETAS remains ≈ 1.0 under MLE, interpret as detector liberalism, not calibration artifact

## References

- Ogata Y. (1998). Space-time point-process models for earthquake occurrences. *Ann. Inst. Stat. Math.*, 50, 379–402.
- Ogata Y. (1988). Statistical models for earthquake occurrences and residual analysis. *J. Amer. Stat. Assoc.*, 83, 9–27.
- Helmstetter A., Sornette D. (2003). Borehole measurements and the scaling of earthquake triggering. *J. Geophys. Res.*, 108, 2477.
