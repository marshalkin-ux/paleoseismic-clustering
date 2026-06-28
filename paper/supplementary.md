# Supplementary material

Extended diagnostics excluded from the primary pipeline (see main text one-line pointers).

## S1. Bird (2003) tectonic-path heuristic

The Bird (2003) plate-boundary model was tested as an alternative distance metric for η-linkage: shortest path along plate boundaries (Dijkstra) with 1.5× great-circle fallback when no path exists.

**Audit (`scripts/generate_grl_figures.py::fig_tectonic_vs_euclidean`, 4987 random pairs):**
- **98%** of pairs use the 1.5× GC fallback (no usable tectonic path).
- Median Δlog₁₀η = **+0.28** on random pairs (tectonic > GC for most samples due to fallback inflation).
- Only **~2%** of boundary-proximal pairs use a real Dijkstra path.

**Conclusion:** unsuitable as a global gate; **excluded from primary inference**. Primary analysis uses great-circle distance only. Failure to validate this metric shows **metric unsuitability**, not evidence against global series.

Figures: `figures/grl/fig05_tectonic_vs_euclidean.png`, `fig07_tectonic_path_usage.png`.

## S2. Catalog-matched WLS (Appendix B detail)

**Reproducibility / coupling illustration only — not used for hypothesis testing.**

Catalog-matched WLS (`scripts/calibrate_etas.py`, `results/etas_calibration.json`): μ ≈ 0.103, K ≈ 0.495, fitted on the same 24 GK aftershocks as the detector path.

Validation (`results/etas_validation.json`, n = 1000, multiseed stable): mean = 27.0, p_ETAS = 1.0, N_obs = 27.

The fitted **K ≈ 0.495 is a catalog-WLS artifact** (detector–calibration coupling on the same catalog); **invalid for inference**. Illustrates why primary null uses temporal MLE (`calibrate_etas_mle.py`).

| Component | Method |
|-----------|--------|
| μ | GK mainshocks / T (closed form) |
| c, p | Omori MLE, Nelder–Mead on 24 delays |
| K, α | WLS (`numpy.linalg.lstsq`) on the same 24 GK aftershocks |
