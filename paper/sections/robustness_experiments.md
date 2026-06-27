# Robustness Experiments Plan

**Project:** paleoseismic-clustering  
**Target:** verify stability of global seismic sequence detection (M≥6.5, 2150 BCE – 2026 CE)  
**Core metric:** η_ij = t_ij · r_ij^1.6 · 10^(−m_i), tectonic distance along Bird (2003) boundaries  
**Baseline:** Monte Carlo validation with 10,000 permutations; FDR correction (Benjamini-Hochberg 1995)

---

## Experiment 3.1 — Sensitivity to Temporal Window

**Hypothesis:** If detected sequences reflect real physical coupling, they should be robustly
detected across a range of temporal windows consistent with known stress-transfer timescales
(months for static Coulomb transfer; years for viscoelastic relaxation).

**Protocol:**

| Step | Detail |
|------|--------|
| Variable | T_window ∈ {30 d, 90 d, 180 d, 1 yr, 2 yr, 5 yr, 10 yr, 20 yr} — 8 values on a log scale |
| Fix | All other parameters at baseline values (N ≥ 4, ≥ 3 tectonic zones, full catalogue) |
| Output | Number of detected sequences S(T_w) and mean p-value as functions of T_window |
| Permutations | 10,000 per T_window value |
| Plot | S(T_w) vs T_window with 95% bootstrap CI (1,000 bootstrap resamples of catalogue) |

**Interpretation thresholds:**

- **Stable signal:** S(T_w) remains significantly above the permutation baseline for
  T_window in [1 yr, 5 yr] → sequences are robust; report this range as preferred.
- **Window-dependent:** S(T_w) peaks sharply at one T_window value → detected sequences
  are an artefact of threshold tuning; classify as inconclusive.
- **Monotonically increasing:** S(T_w) grows with T_window and never plateaus →
  catalogue may not be complete enough to define meaningful temporal clustering.

**Expected outcome (physical reasoning):** Static Coulomb triggering acts on timescales
of months to ~5 years (Dieterich 1994 nucleation time); viscoelastic relaxation extends
this to ~10 years. A genuine signal should therefore be robust for T_window ∈ [1 yr, 5 yr]
and decay relative to the null for T_window > 10 yr as random co-occurrences dominate.

**Computational cost:** ~8 × 10,000 = 80,000 permutations; estimated runtime ~4 h on
a 12-core workstation (parallelise over T_window values).

---

## Experiment 3.2 — Sensitivity to Hybrid Metric Weights

**Hypothesis:** If the tectonic-distance component of the metric is the key discriminator,
results should be significantly better with α > 0 than with α = 0 (pure Euclidean).

**Protocol:**

| Step | Detail |
|------|--------|
| Variable | α ∈ {0.0, 0.1, 0.2, …, 1.0} — 11 values |
| Metric | r_hybrid = (1 − α) · r_Euclidean + α · r_tectonic |
| Fix | T_window = 2 yr, N ≥ 4, ≥ 3 zones |
| Output | (i) Number of detected sequences S(α); (ii) mean η separation between clustered and background pairs; (iii) AUC of ROC curve on synthetic benchmark (see Experiment 3.5) |
| Permutations | 10,000 per α value |

**Key comparisons:**

- α = 0 replicates a standard Euclidean-distance approach (e.g., Zaliapin & Ben-Zion 2008).
- α = 1 uses pure tectonic distance (our primary metric).
- Intermediate values test whether the Euclidean and tectonic components carry complementary information.

**Interpretation thresholds:**

- **Tectonic advantage confirmed:** AUC(α=1) > AUC(α=0) by > 0.05 on synthetic benchmark.
- **Metric not critical:** AUC flat across α → tectonic distance adds no discrimination
  power; report as a robustness finding, not a failure.
- **Intermediate optimum:** AUC peaks at α* ∈ (0, 1) → adopt α* as optimal hybrid weight
  in the revised methodology.

**Note:** α sensitivity also controls for the possibility that tectonic distance is poorly
defined in intraplate settings; events classified as intraplate should be flagged and
analysed separately with α = 0.

---

## Experiment 3.3 — Comparison of Declustering Algorithms

**Hypothesis:** Detected global sequences should not be reducible to aftershock contamination.
If results change substantially with declustering, the detected sequences may be local
aftershock clusters misidentified as global series.

**Three catalogue variants:**

| Variant | Label | Description |
|---------|-------|-------------|
| A | `nodecl` | Full catalogue, no declustering (baseline) |
| B | `GK74` | Gardner & Knopoff (1974) window declustering; space-time windows scale with magnitude |
| C | `ETAS02` | Stochastic declustering via ETAS (Zhuang et al. 2002); each event assigned P(background) via EM algorithm |

**Evaluation metric:**

Use synthetic catalogues with injected clusters of known membership (generated in
Experiment 3.5) to compute:

- **Precision** = TP / (TP + FP) — fraction of detected sequences that are real
- **Recall** = TP / (TP + FN) — fraction of real sequences that are detected
- **F1** = 2 · Precision · Recall / (Precision + Recall)

where TP/FP/FN are defined with respect to injected cluster membership.

**Interpretation thresholds:**

- F1 difference between variants < 0.05 → declustering choice does not affect conclusions.
- F1(`ETAS02`) > F1(`GK74`) by > 0.05 → prefer probabilistic declustering; update pipeline.
- F1 drops substantially with any declustering → re-examine whether global sequences
  are aftershock artefacts; apply cluster radius cut to exclude near-source events.

**Secondary output:** Report the fraction of each detected sequence's events that survive
declustering. Sequences where > 50% of events are removed by both methods should be
flagged as "aftershock-dominated" and excluded from the main count.

---

## Experiment 3.4 — Bootstrap by quality_score

**Hypothesis:** Historical events (pre-1900) with low quality_score may introduce spurious
sequences through magnitude inflation or location error. Results from the high-quality
instrumental sub-catalogue should be consistent with the full catalogue.

**Protocol:**

| Step | Detail |
|------|--------|
| Sub-catalogue A | quality_score > 0.7 (instrumental period, ~1964–2026; ~N_A events) |
| Sub-catalogue B | Full catalogue (2150 BCE – 2026 CE; ~N_B events) |
| Fix | T_window = 2 yr, N ≥ 4, ≥ 3 zones, α = 1 |
| Bootstrap | Draw 1,000 bootstrap resamples of sub-catalogue A with replacement; compute S(bootstrap) distribution |
| Compare | Check whether S(B) lies within the 95% CI of S(A)'s bootstrap distribution |
| Permutations | 10,000 per run |

**Interpretation thresholds:**

- S(full) within 95% CI of S(instrumental bootstrap) → historical data do not inflate
  sequence counts; conclusions are robust to catalogue completeness.
- S(full) > 97.5th percentile of S(instrumental bootstrap) → historical segment inflates
  counts; stratify analysis by epoch and report separately.
- S(full) < 2.5th percentile of S(instrumental bootstrap) → historical events suppress
  detection (e.g., by filling gaps in what would otherwise be detected sequences);
  apply epoch-stratified analysis.

**Additional check:** Rerun with quality_score > 0.5 (partially historical, ~1900–2026)
and quality_score > 0.3 (full historical) to trace the quality-score sensitivity curve S(q_thresh).

---

## Experiment 3.5 — Threshold Calibration via Synthetic Catalogues

**Purpose:** Provide empirical support for the chosen thresholds N_min and zone_min using
synthetic catalogues where ground truth is known.

**Synthetic catalogue generation:**

1. Draw a background Poisson catalogue matching the empirical spatial intensity and
   magnitude-frequency distribution of the real catalogue (Gutenberg-Richter with b
   fitted per tectonic zone; Wiemer & Wyss 2000).
2. Inject M sequences, each consisting of n_seq events drawn from:
   - Time: Omori-law decay (p = 1.1, c = 0.01 d, K = 10) relative to a synthetic mainshock.
   - Location: Gaussian scatter along a synthetic plate boundary segment (σ_r = 50 km).
   - Spanning: randomly assigned to k_seq tectonic zones (k_seq drawn from Uniform[2, 5]).
3. Parameter grid:
   - n_seq ∈ {3, 4, 5, 6} events per sequence
   - k_seq ∈ {2, 3, 4} tectonic zones spanned
   - M ∈ {5, 10, 20} injected sequences per catalogue realisation
   - Repeat 200 realisations per grid cell → 4 × 3 × 3 × 200 = 7,200 synthetic catalogues

**Detection and scoring:**

For each synthetic catalogue, run the full detection pipeline with thresholds
N_min ∈ {3, 4, 5, 6} and zone_min ∈ {2, 3, 4} (a 4 × 3 grid of threshold combinations).
Compute F1 for each combination by comparing detected sequences to injected ground truth
(using ≥ 50% membership overlap as the matching criterion).

**Threshold selection rule:**

Adopt the threshold combination (N_min*, zone_min*) that satisfies:
- F1 > 0.70 averaged over the full parameter grid
- Precision ≥ 0.70 (limit false positives)
- Recall ≥ 0.60 (limit missed sequences)

If multiple combinations satisfy these criteria, prefer the one with highest Precision
(conservative approach appropriate for a detection study where false positives
undermine scientific credibility).

**Output table (example format):**

| N_min | zone_min | F1 (mean) | Precision | Recall | Preferred |
|-------|----------|-----------|-----------|--------|-----------|
| 3 | 2 | 0.61 | 0.52 | 0.74 | — |
| 4 | 3 | 0.74 | 0.78 | 0.71 | ✓ |
| 5 | 3 | 0.70 | 0.84 | 0.60 | — |
| 6 | 4 | 0.55 | 0.90 | 0.41 | — |

**Computational cost:** 7,200 synthetic catalogues × detection pipeline; estimated runtime
~24 h on a 12-core workstation (parallelise over synthetic catalogue realisations).
Recommend running with a reduced grid (200 → 50 realisations per cell) for rapid
prototyping, then full grid for final results.

---

## Summary of Robustness Experiments

| Experiment | Variable | Key Metric | Threshold for Robustness |
|------------|----------|------------|--------------------------|
| 3.1 | T_window | S(T_w) vs null baseline | Stable for T_w ∈ [1 yr, 5 yr] |
| 3.2 | α (metric weight) | AUC on synthetic benchmark | AUC(α=1) > AUC(α=0) + 0.05 |
| 3.3 | Declustering algorithm | F1 on synthetic benchmark | F1 difference < 0.05 across variants |
| 3.4 | quality_score cutoff | S(full) vs S(instrumental) CI | S(full) within 95% CI |
| 3.5 | N_min, zone_min | F1, Precision, Recall on injected sequences | F1 > 0.70, Precision ≥ 0.70 |

All experiments should be reported in the supplementary material with full parameter
tables, code availability (DOI-linked Zenodo archive), and seed values for reproducibility
of all random number generators.
