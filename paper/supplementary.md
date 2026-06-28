# Supplementary material

Extended diagnostics excluded from the primary pipeline (see main text one-line pointers).

## S1. Bird (2003) tectonic-path heuristic

The Bird (2003) plate-boundary model was tested as an alternative distance metric for η-linkage: shortest path along plate boundaries (Dijkstra) with 1.5× great-circle fallback when no path exists.

**Audit (`scripts/generate_grl_figures.py::fig_tectonic_vs_euclidean`, 4987 random pairs):**
- **98%** of pairs use the 1.5× GC fallback (no usable tectonic path).
- Median Δlog₁₀η = **+0.28** on random pairs (tectonic > GC for most samples due to fallback inflation).
- Only **~2%** of boundary-proximal pairs use a real Dijkstra path.

**Conclusion:** excluded from primary pipeline; no synthetic benchmark in this work; comparison deferred to supplementary material and future work. Primary analysis uses great-circle distance only.

Figures: `figures/grl/fig05_tectonic_vs_euclidean.png`, `fig07_tectonic_path_usage.png`.

## S2. Catalog-matched WLS (negative control)

**Reproducibility / coupling illustration only — not used for hypothesis testing.**

Catalog-matched WLS (`scripts/calibrate_etas.py`, `results/etas_calibration.json`): μ ≈ 0.103, K ≈ 0.495, fitted on the same 24 GK aftershocks as the detector path.

Validation (`results/etas_validation.json`, n = 1000, multiseed stable): mean = 27.0, p_ETAS = 1.0, N_obs = 27.

The fitted **K ≈ 0.495 is a catalog-WLS artifact** (detector–calibration coupling on the same catalog); **invalid for inference**. Illustrates why primary null uses temporal MLE (`calibrate_etas_mle.py`).

| Component | Method |
|-----------|--------|
| μ | GK mainshocks / T (closed form) |
| c, p | Omori MLE, Nelder–Mead on 24 delays |
| K, α | WLS (`numpy.linalg.lstsq`) on the same 24 GK aftershocks |

| Parameter | Catalog fit | H&S 2003 defaults |
|-----------|-------------|-------------------|
| μ (day⁻¹) | 0.103 | 0.008 |
| K | 0.495 | 0.08 |
| α | 0.063 | 1.0 |
| c (day) | 10⁻⁴ | 0.005 |
| p | 1.36 | 1.1 |

## S3. Pre-1900 NOAA records

**47** fragmentary paleoseismic/historical M≥6.5 records from NOAA NGDC are retained in `data/processed/unified_catalog_full.csv` for provenance. **Not removed from CSV**; a separate pipeline re-run excluding them **was not performed**.

These 47 events are **excluded from the primary detector pipeline and ETAS calibration window**: the canonical pipeline (`pipeline_v2.py`) and ETAS fit use the modern catalog **1973–2026 only** (*N* = 2041). Epoch-stratified counts in Results §4.1 include pre-1900 descriptively via `run_full_historical_analysis.py` but do not enter primary significance claims.

- **quality_score:** 0.30–0.60 (metadata, not an inclusion filter).
- **Detector:** 5 algorithmic candidates on this epoch; permutation p = 0.46 — **not statistically significant**.
- **Primary significance path:** detector + ETAS + permutation claims — **1900–2026** (descriptive) and **1973–2026** (primary); pre-1900 is **outside** primary inference.
