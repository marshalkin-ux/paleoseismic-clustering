# Global Seismic Series: Statistical Analysis of Spatiotemporal Clustering in M≥6.5 Earthquake Catalogs, 1973–2026 CE

*…with extrapolation to the early instrumental period (1900–1972). Merged NOAA+USGS catalog; 4,267 M≥6.5 events (4,418 CSV rows).*

**DOI:** pending registration

© 2026 **Yaroslav Marshalkin**

---

## Metadata

**Author:** Yaroslav Marshalkin  
**Email:** marshalkin@gmail.com · **Telegram:** [@MRSHLKN](https://t.me/MRSHLKN)  
**Repository:** [github.com/marshalkin-ux/paleoseismic-clustering](https://github.com/marshalkin-ux/paleoseismic-clustering)  
**Interactive demo:** [marshalkin-ux.github.io/paleoseismic-clustering](https://marshalkin-ux.github.io/paleoseismic-clustering/)  
**Russian version:** [article_ru.md](article_ru.md) · [article_ru.pdf](article_ru.pdf)

---

## Abstract

We analyze an **analysis catalog of 4,267 unique M≥6.5 events**[^catalog-n] (modern window 1973–2026: 2,041 events); historical NOAA records (*n*=47) are reported in **Appendix A** only. A Baiesi–Paczuski η detector with **great-circle distance** yields **27 algorithmic candidates** in the modern window. **Catalog-calibrated temporal ETAS** (GK mainshocks, 1973–2026): mean = 27.0, **p_ETAS = 1.0** — N_obs is consistent with the null. Under the temporal ETAS model used, we find no anomalous temporal clustering beyond catalog-calibrated ETAS; the spatial component was not modeled, so questions of long-range spatial linkage remain open. **Limitation:** spatial component not modeled (§5.6).

[^catalog-n]: Canonical analysis N: **4,267** unique M≥6.5 after deduplication (±30 days, ≤50 km; ISC > USGS > NOAA; cf. Waldhauser & Schaff, 2008). **4,418** saved CSV rows include ~151 NOAA M<6.5 rows (provenance only).

**Keywords:** global seismicity; seismic series; earthquake clustering; Baiesi–Paczuski metric; ETAS validation; paleoseismology; Flinn–Engdahl

> **Terminology.** *Detector candidate* — algorithmic output (N≥4, M≥6.5, mean pairwise GC >1500 km, merged from sliding windows). *Series* in tables denotes such a candidate, **not** a validated physical chain. *Validated global chain* would require a physical mechanism and confirmation beyond the primary calibrated ETAS null; none established.

---

## 1. Introduction

Large earthquakes do not occur as independent [Poisson](https://en.wikipedia.org/wiki/Poisson_point_process) events. Following the 1992 Landers earthquake (Mw 7.3), Hill et al. (1993) documented remotely triggered seismicity at distances exceeding 1,000 km. Brodsky & Prejean (2006) showed that surface waves can initiate swarms in volcanic systems thousands of kilometres away. After the 2004 Sumatra–Andaman earthquake (Mw 9.1), elevated activity was reported in distant regions; possible mechanisms were discussed earlier (Pollitz et al., 1998; Freed & Lin, 2001) — **correlation within series S170 does not establish causality**.

However, the systematic nature of such correlations remains debated. Michael (2011) tested whether global M≥7 clustering in 1995–2011 exceeds Poisson rate fluctuations. Shearer & Stark (2012) tested whether global M≥7 and M≥8 rates increased after the 2004 Sumatra event. Kagan & Jackson (1999) confirmed elevated probability of paired events at short separation without resolving long-range links.

The [ETAS](https://en.wikipedia.org/wiki/Epidemic-type_aftershock_sequence) model (Ogata, 1988) reproduces regional aftershock clustering but does not encode inter-plate correlations. Prior global tests often used plug-in regional parameters (Helmstetter & Sornette, 2003); here the **primary null** is catalog-calibrated temporal MLE on GK mainshocks (§3.7). The [Baiesi–Paczuski](https://en.wikipedia.org/wiki/Earthquake_clustering) (2004) metric and Zaliapin–Ben-Zion extensions (2008, 2013) provide objective cluster detection but typically use Euclidean distance, ignoring lithospheric connectivity.

**Objective.** Test (and if warranted, **falsify**) the hypothesis that physically meaningful multi-regional “global series” exist, with **primary inference on the modern window (1973–2026)**, using complementary null tests (permutation vs ETAS) and explicit detector liberalness assessment.

**Scope.** We combine nearest-neighbor clustering with great-circle distance and ETAS null-model validation; this extends prior global rate tests (Michael 2011; Shearer & Stark 2012) with a complementary η-linkage statistic but does not supersede their conclusions.

### 1.1 Research question and testable hypotheses

**Research question (RQ):** Do physically meaningful multi-regional global series exist in the M ≥ 6.5 catalog (primary window 1973–2026)?

**Scope.** The **primary ETAS test** addresses **temporal** excess clustering in 2-yr detector windows only; it does **not** apply a spatial Ogata (1998) kernel and therefore does **not** test whether geographically dispersed candidates (mean GC > 1500 km) form a **physically linked** global series. That spatial linkage question requires spatial ETAS calibration (future work). We retain the title's spatiotemporal framing for the detector and η-metric, but conclusions are limited accordingly (§5.6).

Four distinct statistical targets must not be conflated (table below; see also §3.8).

| Test / hypothesis | H₀ (null) | H₁ (alternative) | Statistic | Result (modern) |
|-------------------|-----------|------------------|-----------|-----------------|
| **(a) Permutation** | Event times **independent** (Poisson process, fixed coordinates) | Times **dependent** (clustering) | mean log₁₀(η_NN); n = 10,000 | **Reject H₀:** p = 0.0001 (1/10,001) |
| **(b) ETAS-null (primary MLE)** | N_series ≤ **catalog-calibrated** temporal ETAS expectation (GK mainshocks) | N_series **exceeds** calibrated ETAS | series count in 1000 synthetic catalogs | **Do not reject H₀:** p_ETAS = 1.0; N_obs = 27 = mean = 27.0 |
| **(c) Global series** | **No** physically meaningful multi-regional series (no mechanism; liberal detector) | Teleseismic chains explainable by physics | detector + mechanism + null tests | **Not tested by temporal-only ETAS**; detector candidates lack validated physical mechanism; spatial null open |
| **(d) WLS negative control** (App. B) | Detector--calibration coupling artifact on same catalog | — | p_ETAS = 1.0, mean = 27 = N_obs | Coupling illustration; **not** primary null |

**Methodological statement (permutation):** rejecting H₀ in test (a) does **not** confirm global series or teleseismic triggering — it rejects Poisson time independence only (expected with aftershocks; Ogata, 1988).

**Methodological statement (ETAS):** p_ETAS = 1.0 under calibrated MLE means **N_obs = 27 is consistent** with synthetics — the detector finds no excess series relative to the catalog-calibrated null; this does **not** confirm test (c). Validity depends on temporal-only MLE (no Ogata 1998 spatial kernel). WLS — **Appendix B** (negative control).

---

## 2. Data

### 2.1 Catalog compilation

**Magnitude notation.** Catalog thresholds and detector gates use **M ≥ 6.5** (USGS ComCat, predominantly M_w); individual events are cited with catalog type where relevant (e.g. M_w 7.3).

| Source | Period | Role |
|--------|--------|------|
| USGS ComCat | 1900–2026 | Primary instrumental catalog |
| ISC Bulletin | 1900–2023 | Relocated hypocenters for verification |
| NOAA NGDC | pre-1900 | Historical/paleoseismic records (47 events — Appendix A) |

Duplicate records were merged using ±30 days and ≤50 km spatial tolerance (cf. Waldhauser & Schaff, 2008; common catalog-merge practice); source priority: ISC > USGS > NOAA. After deduplication, the catalog contains **4,267** unique M≥6.5 events (from **4,418** saved CSV rows). **151 sub-threshold rows** (NOAA, M<6.5 from the M≥6.0 fetch) **are retained in CSV for provenance but excluded from all clustering and series-detection steps**.

**Canonical count summary (all sections)**

| Layer | Count | Note |
|-------|------:|------|
| Raw merged CSV | 4,418 | includes ~151 NOAA M<6.5 (provenance only) |
| Analysis catalog | **4,267** | unique M≥6.5; all clustering |
| Modern window | **2,041** | 1973–2026 |
| Detector candidates | **47** (27 modern) | **not** discoveries |

**Table: Catalog merge reconciliation**

| Stage | Count | Notes |
|-------|------:|-------|
| CSV rows saved | 4,418 | Includes ~151 events M<6.5 from NOAA (M≥6.0 fetch) |
| Excluded from analysis (M<6.5) | ~151 | Provenance in CSV; not used in clustering |
| Unique M≥6.5 after dedup | 4,267 | ±30 days, ≤50 km; **analysis catalog** |
| USGS ComCat raw (1973–2026) | 2,088 | Legacy instrumental catalogue |
| Modern window after merge/ISC | 2,041 | Full merged catalog |
| Declustering (primary) | GK mainshocks (modern) | 2,017/2,041 (~24 aftershocks, 98.8%) |
| ZBZ sensitivity (supplement) | 2,040/2,041 | 1 dependent event; separate run only |

**Quality scoring (metadata).** Each event receives a quality_score in [0.30, 0.95] based on epoch, phase readings, and cross-catalog overlap (Woessner & Wiemer, 2005); this is interpretive metadata, **not** an inclusion filter. Instrumental events after 1960 typically score ≥0.90; pre-1900 documentary records score 0.30–0.60.

**Final analysis catalog:** 4,267 unique M≥6.5 events (4,418 CSV rows = raw merged file, not analysis N). **Primary analysis set:** events **1900–2026** (4,218); **47 pre-1900 records** stay in CSV (provenance) but are **excluded from the primary detector pipeline and ETAS calibration window** (1973–2026 only) — see **Appendix A** (no re-run excluding them from CSV).

| Epoch | Events M≥6.5 | Period |
|-------|---------------|--------|
| Early instrumental | 2,179 | 1900–1972 |
| Modern | 2,041 | 1973–2026 |
| Pre-1900 (provenance) | 47 | Appendix A |

### 2.2 Catalog completeness

Maximum-curvature analysis yields Mc = 6.55. Maximum-likelihood b-value from 1,688 events above Mc:

**b = 0.911 ± 0.018**

The [Gutenberg–Richter](https://en.wikipedia.org/wiki/Gutenberg%E2%80%93Richter_law) relation is satisfied above Mc. **b-value consistency:** clustering η uses **b = 1.0** per the Baiesi & Paczuski (2004) convention for cross-catalog comparability; the Monte Carlo null and completeness analysis use the fitted **b = 0.911 ± 0.018**. This difference is intentional: η is a relative connectivity measure, not a rate forecast.

### 2.3 Clustering and detector criteria (canonical list)

Single list for Methods and Results (`src/analysis/clustering.py`, `pipeline_v2.py`):

1. **GK declustering** (primary) → mainshocks for η NN forest.
2. **η NN forest:** i* = argmin ηij; **b = 1.0**, **r^1.6** (Baiesi–Paczuski 2004); rij = **great-circle distance** (km).
3. **Sliding windows:** 1, 2, 5 yr (1-yr step).
4. **Merge:** 142 window candidates → **47** merged.
5. **Detector gate (sole mandatory criteria):** N ≥ 4, M ≥ 6.5, **mean pairwise GC > 1500 km** (`results/clustering_gc1500.json`).
6. **Flinn–Engdahl zone count — diagnostic/reporting only**, not an admission criterion (legacy ≥3 FE threshold gave the same N = 27 on the modern window).

---

## 3. Methods

Unified pipeline (see §3.3 for detector algorithm): **Data** → **Deduplication** (±30 d, ≤50 km) → **η metric** → **GK declustering** (primary) → **series detection** (GC >1500 km) → **statistical tests** (permutation, ETAS, FDR).

### 3.1 Data and deduplication

Catalog sources and merge reconciliation are in §2.1. Duplicates merged at ±30 days and ≤50 km (cf. Waldhauser & Schaff, 2008); ISC > USGS > NOAA priority. **Analysis catalog: 4,267** unique M≥6.5 (4,418 CSV rows = provenance only).

### 3.2 Tectonic distance heuristic (deprecated diagnostic)

The Bird (2003) tectonic-path heuristic is **excluded from primary inference** (Appendix diagnostic only); **primary analysis uses great-circle distance only** for η-linkage and series detection (§3.4). **Failure to validate** this metric at global scale (98% 1.5× GC fallback) shows the metric is **unsuitable**, **not** evidence against global series.

### 3.3 η connectivity metric

Following Baiesi & Paczuski (2004) and Zaliapin et al. (2008):

**ηij = tij · rij^1.6 · 10^(−b·mi)**

| Component | Symbol | Physical meaning |
|-----------|--------|------------------|
| Time | tij (yr) | Penalty for large temporal separation |
| Distance | rij^1.6 (km) | Great-circle separation (primary pipeline) |
| Magnitude | 10^(−b·mi) | Weighting by parent-event magnitude mi |

Here df = 1.6 (fractal dimension; Baiesi & Paczuski, 2004) and **b = 1.0** (code default `B_DEFAULT`; parent magnitude mi only—no erroneous bi in the exponent). Smaller η indicates tighter spatiotemporal coupling.

*Note:* b = 1.0 and df = 1.6 follow Baiesi & Paczuski (2004) for cross-study η comparability — a **deliberate simplification**, not calibrated to our catalog. The empirical b = 0.911 ± 0.018 (Mc, completeness, Monte Carlo null) is **not** used in the η formula. **b sensitivity at fixed detector gates** (`results/sensitivity_b_eta0.json`): b = 1.0 and b = 0.911 → **N_series = 27** (2 yr, mean GC > 1500 km, N ≥ 4). **Equal N = 27 does not prove candidate identity:** `global_series()` does not use b (Jaccard of series event sets = 1.0; `results/sensitivity_b0911_series_overlap.json`); upstream `identify_clusters()` at b = 0.911 was **not** re-run (~9.8% of events change cluster labels when b changes).

**Units note.** η is a relative connectivity measure without absolute physical units; only ratios and log10(η) statistics are interpreted. The threshold η₀ is determined by Zaliapin–Ben-Zion KDE valley detection between bimodal modes in log₁₀(η) (Zaliapin & Ben-Zion, 2013); default η₀ = 10^(median log₁₀ η). Visual verification of bimodality was limited at global M≥6.5 scale (§3.6).

### 3.4 Global-series detector algorithm

Implementation: `src/analysis/clustering.py` (`SeismicClusterAnalyzer`), orchestrated by `src/analysis/pipeline_v2.py`, ETAS by `src/analysis/etas_validation.py`. **Output = algorithmic candidates**, not physical discoveries.

| Step | Module / function | Content |
|------|-------------------|---------|
| 1 | `GardnerKnopoffDeclustering` | GK on M≥6.5 → **2,017** mainshocks (24 aftershocks removed from 2,041) |
| 2 | `find_nearest_neighbor` | η NN forest: i* = argmin ηij; rij = **great-circle distance** (km); **b=1.0, r^1.6** — not catalog-calibrated |
| 3 | `global_series` | Sliding windows **1, 2, 5 yr** (1-yr step): anchor t, window [t, t+Δt] |
| 4 | epoch merge | Overlapping candidates merged → **47** merged (142 windows before merge) |
| 5 | Criteria | N ≥ 4, M ≥ 6.5, mean pairwise GC > 1500 km (`clustering_gc1500.json`) |
| 6 | Permutation | Global **mean log10(ηNN)**, n = 10,000; H0 = independent event times |
| 7 | ETAS null | Temporal MLE primary; p_ETAS = 1.0, mean = 27.0 (modern window) |
| 8 | Output | Candidate list + FDR post-hoc (not a discovery claim) |

```
catalog M≥6.5 (4267) → GK mainshocks → η NN forest → windows 1/2/5 yr
  → merge overlapping → filter (N≥4, mean GC>1500 km) → candidates → MC + ETAS
```

**Detector candidate (formal):** merged group with N ≥ 4, M ≥ 6.5, mean pairwise GC > 1500 km from sliding windows (1/2/5 yr).

#### 3.4.1 Algorithm specification

Code-accurate definitions (`declustering.py`, `clustering.py`, `pipeline_v2.py`, `run_clustering_gc1500.py`):

**Gardner–Knopoff.** `WINDOWS` table: M → (T[days], R[km]); linear interpolation; **magnitude-descending** iteration; aftershocks dt ∈ [0, T], foreshocks dt ∈ [−T/2, 0); haversine distance ≤ R.

**`find_nearest_neighbor`.** Causal argmin η_ij: η = t_ij · r_ij^1.6 · 10^(−b·m_i); t_ij in years, r_ij = great-circle km, b = 1.0.

**`identify_clusters`.** Union–Find for η < η₀; η₀ from KDE valley of log₁₀(η) or median fallback; clusters with <2 events → background.

**`global_series`.** Greedy `used[]` mask; anchor loop; window [t_i, t_i+Δt); gates min_events, min_magnitude, mean pairwise GC > 1500 km; accepted events marked used — no further windows from them.

**Merge.** Runs at 1/2/5 yr plus epoch-specific windows yield **142** window hits; union of overlapping event sets → **47** merged (27 modern). Stopping: no new windows from unused anchors.

### 3.5 Declustering and pipeline

```
Raw catalogs (USGS / ISC / NOAA)
        ↓
   Dedup (±30 d, ≤50 km)
        ↓
   Exclude M<6.5 (~151 NOAA rows) → 4,267 unique M≥6.5
        ↓
 GK declustering (primary) → mainshocks for η NN forest
        ↓
 η NN forest (great-circle distance)
        ↓
 Sliding windows (1 / 2 / 5 yr)
        ↓
 Merge overlapping groups
        ↓
 Series criteria (N≥4, M≥6.5, mean GC>1500 km)
        ↓
 MC / ETAS / FDR validation
```

**Primary declustering (GK only in reporting pipeline).** In the canonical pipeline (`pipeline_v2.py`, `decluster_method='gardner_knopoff'`), **Gardner–Knopoff (GK) is the sole primary** pre-processing step: mainshocks feed the η NN forest and sliding-window series search. For the modern window (1973–2026), GK removes ~24 local aftershocks (2,017/2,041, 98.8%). The epoch script `run_full_historical_analysis.py` (47 series across epochs) applies `global_series()` to the full M≥6.5 list **without** an explicit GK pre-filter; GK counts in Table §2.1 come from `run_declustering_comparison.py`.

**ZBZ — supplement/sensitivity only.** Zaliapin–Ben-Zion (2040/2,041 independent) is reported **only as a sensitivity check** in supplementary comparison (`run_declustering_comparison.py`), not as a co-primary or sequential filter. **ZBZ does not replace GK** and is not applied sequentially with it.

**Why GK removes 24 events but ZBZ removes 1 (not a contradiction).** The algorithms use different criteria on the same global M≥6.5 catalog (2,041 events, 1973–2026):

| Aspect | Gardner–Knopoff (primary) | Zaliapin–Ben-Zion (sensitivity) |
|--------|---------------------------|----------------------------------|
| Mechanism | Fixed magnitude-dependent time/space windows (1974 table; ~22 d / ~61 km at M≥6.5) | Nearest-neighbor η metric + KDE valley threshold on log₁₀(η) |
| Scale sensitivity | Designed for regional catalogs; flags short-range fore/aftershocks within windows | At global M≥6.5 scale, events are sparse → most η values are high → permissive |
| Dependent events | **24** (2,017 mainshocks) | **1** (2,040 mainshocks) |

GK applies conservative local window rules; ZBZ classifies only events with exceptionally low η to a predecessor. The 23-event gap reflects **algorithm and parameter choice**, not conflicting physics. **GK is primary for all inference** (pipeline, ETAS calibration, reported counts). **Quantitative sensitivity** (`scripts/run_declustering_sensitivity.py`, `results/sensitivity_declustering.json`): under fixed gates (2 yr, mean GC > 1500 km, N ≥ 4), **GK, ZBZ, and no declustering all yield N = 27**. Empirically N = 27 is **stable under three declustering choices** for our fixed detector gates; this **does not prove** declustering is immaterial in general — algorithms assign **different mainshock labels** (24 vs 1 removed) and could matter under other thresholds.

**Declustering sensitivity (modern window, N_series):**

| Method | Role | Events | Removed | N_series | Δ vs GK |
|--------|------|-------:|--------:|---------:|--------:|
| Gardner–Knopoff | Primary | 2,017 | 24 | **27** | 0 |
| Zaliapin–Ben-Zion | Sensitivity | 2,040 | 1 | **27** | 0 |
| None | Sensitivity | 2,041 | 0 | **27** | 0 |

### 3.6 Threshold η₀

1. **Declustering** via [Gardner–Knopoff](https://en.wikipedia.org/wiki/Aftershock) (1974) — mainshocks for NN search.
2. **Nearest-neighbor forest:** for each event j, parent i* = argmin ηij.
3. **Threshold η₀:** KDE valley detection between bimodal modes in log₁₀(η) (Zaliapin & Ben-Zion, 2013); fallback η₀ = 10^(median log₁₀ η). Distribution and threshold — `figures/grl/fig_eta_threshold.png` (`scripts/plot_eta_threshold.py`, `results/eta_threshold_meta.json`). **Limitation:** at global M≥6.5 scale bimodality is weak; KDE stability **not verified** — see figure caption.
4. **η₀ scope split:** η₀ affects the **GK/ZBZ declustering path** (`identify_clusters()`), **not** **N_obs = 27** — `global_series()` counts without η₀ filtering. η₀ ±20% — `not_applied` (`results/sensitivity_b_eta0.json`); future work via `pipeline_v2`.

**Why η₀ is not applied in the main series path.** The KDE-derived η₀ threshold applies only to `identify_clusters()` in the GK/ZBZ declustering path. The reported **N_obs = 27** from `global_series()` uses fixed gates (2 yr window, mean GC > 1500 km, N ≥ 4) **without** η₀ filtering. Therefore the unverified η₀ status affects declustering labels, not the reported series count directly. Future work (`pipeline_v2`) will integrate η₀ into the series-detection path.
5. **Detector criteria** — §2.3 (N≥4, M≥6.5, mean GC>1500 km); FE counts diagnostic only.

### 3.7 Primary ETAS null (temporal MLE)

**Primary inference** uses **catalog-calibrated** temporal Ogata (1988) MLE on GK mainshocks (`scripts/calibrate_etas_mle.py`, `results/etas_mle_calibration.json`): μ ≈ 0.097, K ≈ 10⁻⁴, α ≈ 0.25, c = 0.001 day, p ≈ 1.91. Validation: `scripts/run_etas_validation.py` → `results/etas_validation.json` (mean = 27.0, p_ETAS = 1.0, N_obs = 27).

WLS (`scripts/calibrate_etas.py`, `results/etas_calibration.json`) — **Appendix B** negative control. Spatial Ogata (1998) MLE — future work (`docs/future_work_etas_mle.md`).

Multi-seed ETAS (MLE primary): seeds 42–51, n = 1000 catalogs/seed (`scripts/run_etas_multiseed.py`, `results/etas_multiseed.json`).

### 3.8 Statistical validation

#### What each test checks

**Methodological statement (permutation):** p = 0.0001 rejects **Poisson event times only**; does **not** confirm global series; expected for aftershock catalogs (Ogata, 1988).

| Test | Null hypothesis | Role | Interpretation |
|------|-----------------|------|----------------|
| **ETAS MLE (primary)** | N_obs consistent with calibrated ETAS | **Primary** | mean = 27.0, p_ETAS = 1.0 — no excess series; does not confirm global-series hypothesis |
| **Permutation** (n = 10,000) | Globally Poissonian event times | Secondary | Rejects temporal independence; expected for aftershock catalogs |
| **Benjamini–Hochberg** | — | Post-hoc | Not a discovery claim |

#### Multiple comparisons

Post-hoc demonstration of the [Benjamini–Hochberg](https://en.wikipedia.org/wiki/False_discovery_rate) procedure on **N = 47** merged-series p-values (after sliding windows 1/2/5 yr, merge, and series criteria N ≥ 4, M ≥ 6.5, mean GC > 1500 km; see `results/fdr_correction_results.csv`): **45/47** at q = 0.05. This **does not** correct the 142 window candidates × search parameters and is **not** a discovery claim — detector sensitivity only (see §5.7).

**ETAS null model (primary MLE).** Synthetic catalogs with **calibrated** temporal MLE parameters. On the real modern catalog the algorithm finds **N_obs = 27** series.

**Single-seed run (seed = 42, n = 1000):** mean = **27.0**, **p_ETAS = 1.0** — N_obs **consistent** with calibrated ETAS expectation.

**Primary ETAS null (table below).**

| Null model | μ | K | Mean | p_ETAS | Interpretation |
|------------|--:|--:|-----:|-------:|----------------|
| Temporal MLE (primary) | ≈0.097 | ≈10⁻⁴ | 27.0 | 1.0 | N_obs consistent with calibrated null; no excess series |

**Sensitivity: α fixed to catalog b = 0.911** (`results/etas_calibration_b0911.json`, `results/etas_validation_b0911.json`): K refitted to **≈0.358**; MLE primary conclusion unchanged (p_ETAS = 1.0).

| Test | Parameters | Result |
|------|------------|--------|
| Permutation ([Monte Carlo](https://en.wikipedia.org/wiki/Monte_Carlo_method)) | n = 10,000 | p = 0.0001 (1/10,001)[^mc-p], z = −6.17 (modern) |
| ETAS null (MLE primary) | μ ≈ 0.097, K ≈ 10⁻⁴; 1000 cat.; N_obs = 27 | mean = 27.0; p_ETAS = 1.0 |
| Declustering (primary) | GK | 2,017/2,041 (24 aftersh.) |

**Verified from code.** Series counts and epoch p-values: `results/analysis_full_historical.json`. Monte Carlo (p, z): `results/montecarlo_full.json`. ETAS (FPR, p_ETAS): `results/etas_validation.json`. GK/ZBZ counts: `scripts/run_declustering_comparison.py`. Tectonic diagnostic (median Δlog₁₀η = +0.28): `scripts/generate_grl_figures.py::fig_tectonic_vs_euclidean`.

---

## 4. Results

### 4.1 Detector candidates (not “discovered series”)

**47 algorithmic candidates** after merge (142 window candidates before merging). These are **detector outputs** (see §5.7), not validated physical episodes:

| Epoch | N series | Events | p-value | z-score |
|-------|----------|--------|---------|---------|
| Modern (1973–2026) | 27 | 2,041 | 0.0001 (1/10,001) | −6.17 |
| Early instrumental (1900–1972) | 15 | 2,179 | 0.007 | −2.43 |
| Historical (pre-1900) | 5 | 47 | 0.46 | — |

**Modern period.** Twenty-seven candidates; primary ETAS MLE: mean = 27.0, p_ETAS = 1.0, N_obs = 27.

**Key results summary (modern window).** Within the temporal ETAS model used, the observed cluster count (27) does not differ from random (p = 1.0). This does not confirm the hypothesis of global spatiotemporal series; however, a definitive conclusion requires spatiotemporal ETAS (Ogata, 1998), which is beyond the scope of this work.

**Early instrumental period.** Fifteen series, p = 0.007; quality_score < 0.7 before 1960.

**Historical period (pre-1900):** five candidates; p = 0.46 — **not used for significance claims**; see **Appendix A**.

*Interpretation of permutation, ETAS, and global-series tests — §5.1–5.4.*

### 4.2 Top-5 detector candidates

> **Table 1 — Top-5 detector candidates** (not ETAS-validated physical series). Entries are algorithmic outputs; primary ETAS MLE null: p_ETAS = 1.0, mean = 27.0.

| Series | N | Regions | Mmax | Period | lat° | lon° |
|--------|--:|--------:|-----:|--------|------|------|
| 1905–1910 | 193 | 43 | 8.8 | 1905–1910 | −60…72 | −180…180 |
| S047 | 53 | 5 | 8.0 | 1982–2024 | −21.5…18.9 | −175.5…155.2 |
| S170 | 46 | 12 | 9.1 | 2002–2023 | −14.3…33.8 | −113.1…167.3 |
| S095 | 25 | 4 | 7.9 | 1989–2017 | −8.1…16.5 | 120.4…146.4 |
| S116 | 22 | 5 | 8.2 | 1993–2021 | −31.7…10.8 | −179.5…179.4 |

The **1905–1910** episode (193 events, 43 regions) is the **largest candidate in the early instrumental window**; catalog completeness before ~1960 is poor (quality_score < 0.7) — **not** “largest series of all time.” **S170** is a modern-window detector candidate (12 Flinn–Engdahl regions, including 2004 Sumatra M 9.1); a descriptive example, not a validated physical series (Figures 1–2 in the repository).

### 4.3 Spatial–temporal distribution

Elevated **detector candidate frequency** (not validated physical series) occurs in 1952–1965 and 2002–2016 (post-Sumatra period). Spatially, candidates concentrate along the circum-Pacific belt (Kamchatka, Kuril Islands, Japan, Tonga, Indonesia). The tectonic-vs-Euclidean diagnostic (§3.2) reports median Δlog₁₀η = +0.28 on random pairs; this reflects the 1.5× GC fallback for most samples, not a validated η₀ shift.

### 4.4 Consolidated sensitivity table (modern window)

Sources: `sensitivity_eta_windows_gc.json`, `sensitivity_b_eta0.json`, `sensitivity_declustering.json`, `clustering_sensitivity_strict.json` (`scripts/run_clustering_sensitivity.py`, `run_declustering_sensitivity.py`).

| Parameter | Setting | N_series |
|-----------|---------|--------:|
| GC gate | 1000 km | 27 |
| GC gate | 1500 km (baseline) | 27 |
| GC gate | 2000 km | 27 |
| Window | 1 yr | 53 |
| Window | 2 yr (baseline) | 27 |
| Window | 5 yr | 11 |
| Window | 10 yr | 6 |
| b in η | 1.0 (BP 2004) | 27 |
| b in η | 0.911 (catalog) | 27 |
| b overlap (series sets) | Jaccard = 1.0; upstream ~9.8% label mismatch | 27 |
| Declustering | GK / ZBZ / none | 27 / 27 / 27 |
| min_events (strict) | 5 / 6 / 8 | 27 / 27 / 27 |
| Catalog | GK mainshocks only | 27 |
| η₀ ±20% | not_applied | — |

η₀ (KDE valley ≈ 7.1×10⁻⁶) affects **GK/ZBZ `identify_clusters()`**, **not** N_obs = `global_series()`; ±20% — future work via `pipeline_v2`.

---

## 5. Discussion

### 5.1 Reconciling null models (permutation vs ETAS)

The two null tests **do not contradict** each other — they target **different hypotheses**:

| Test | Null hypothesis | Result | Interpretation |
|------|-----------------|--------|----------------|
| **Permutation** (n = 10,000) | Globally **Poissonian event times** with fixed coordinates | p = 0.0001 (1/10,001), z = −6.17 | Rejects temporal independence; expected with aftershocks/local clustering |
| **ETAS MLE (primary)** | N_obs consistent with calibrated ETAS | mean = 27.0, p_ETAS = 1.0 | Detector finds no excess series; does not confirm global-series hypothesis |

**Explicit:** rejecting the Poisson permutation null **≠** evidence for teleseismic/global triggering.

### 5.2 Statistical sensitivity vs physical mechanism

### 5.3 Three-layer test interpretation

**Primary conclusion.** Within the temporal ETAS model used, the observed cluster count (27) does not differ from random (p = 1.0). This does not confirm the hypothesis of global spatiotemporal series; however, a definitive conclusion requires spatiotemporal ETAS (Ogata, 1998), which is beyond the scope of this work.

| Layer | p | Interpretation |
|-------|---|----------------|
| Permutation | 0.0001 | Rejects Poisson times; temporal clustering; **not** global chains |
| ETAS MLE (primary) | 1.0 | N_obs = 27 = mean = 27; no excess **temporal** clustering in detector windows |
| Global-series hypothesis | — | **Not tested** by temporal-only ETAS; dispersed candidates; spatial null open |

**WLS negative control (Appendix B):** p_ETAS = 1.0, mean = 27 = N_obs — coupling illustration; **not** primary null.

**Established:** under **primary temporal MLE**, p_ETAS = 1.0 — N_obs = 27 consistent with catalog-calibrated ETAS; no excess temporal clustering in detector windows.

**Not established/tested:** physical teleseismic linkage of dispersed clusters (mean GC > 1500 km); spatial null not applied; no validated mechanism.

**Early instrumental period (1900–1972).** Fifteen series reach p = 0.007 (z = −2.43), but quality_score < 0.7 before 1960 limits interpretation of individual episodes (including 1905–1910).

**Reconciliation with Michael (2011) and Shearer & Stark (2012).** Michael tested complementary Poisson **rate** nulls for global M≥7 clustering; Shearer & Stark tested whether post-2004 **event rates** increased. Our η-linkage test adds a **different statistic** (multi-regional nearest-neighbor structure) but **does not supersede** their conclusions about rates and short-window clustering models. The findings are complementary, not contradictory.

The tectonic diagnostic (§3.2; median Δlog₁₀η = +0.28) quantifies the GC-fallback penalty on random pairs; only **~2%** of audited boundary-proximal pairs use a real Dijkstra path (§3.2)—the metric adds limited value beyond Euclidean distance for most pairs.

### 5.4 Working hypotheses (future work, not claims)

Correlative η links **do not prove** any single mechanism. Possible (unverified) explanations for long-range coupling include:

- **Viscoelastic mantle coupling** — stress redistribution over months to years after major ruptures (Pollitz et al., 1998).
- **Dynamic triggering by surface waves** — short-lived activation at thousands of kilometres (Hill et al., 1993; Brodsky & Prejean, 2006).
- **Shared tectonic loading / stress redistribution** — secular loading without direct triggering (Freed & Lin, 2001).

Co-occurrence within a series may reflect any of these (or other) processes, or catalog artifacts.

### 5.5 ETAS null limitations

**Primary null** — temporal MLE on GK mainshocks (`calibrate_etas_mle.py`, `etas_mle_calibration.json`); WLS — Appendix B only (negative control). See §5.6.

### 5.6 Limitations

**We used temporal ETAS only; the spatial component was not modeled; conclusions are strictly limited to temporal clustering.**

Rejecting "global series" as a **tested** null would require spatial ETAS with an explicit long-range kernel (Ogata 1998); we **do not** claim that rejection here.

| Limitation | Affected step | Impact on main conclusion |
|------------|---------------|---------------------------|
| η₀ unverified at global scale | GK/ZBZ `identify_clusters()` | KDE valley of log₁₀(η_NN), η₀ ≈ 7.1×10⁻⁶; weak bimodality at M≥6.5; `global_series` skips η₀ → N = 27 stable; mis-specified η₀ shifts GK/ZBZ labels only |
| b = 1.0 vs 0.911 in η | η upstream | N_series = 27 both; Jaccard of series sets = 1.0 (`sensitivity_b0911_series_overlap.json`); upstream ~9.8% label mismatch; `identify_clusters()` at b = 0.911 not re-run |
| No spatial Ogata MLE | ETAS null | Temporal MLE primary; spatial MLE — future work |
| 142 windows + merge | Detector | Main source of liberalness |
| Calibrated p_ETAS = 1.0 | ETAS test | No excess temporal clustering; spatial linkage not tested |

**Impact analysis.** If the KDE-derived η₀ threshold were mis-specified at global M ≥ 6.5 scale, GK/ZBZ declustering labels could shift, but the reported series count N = 27 is computed by `global_series()`, which does **not** apply η₀ filtering; the main negative conclusion is therefore stable to η₀ uncertainty on this path. Holding detector gates fixed, substituting catalog b = 0.911 for the BP (2004) b = 1.0 convention in η also leaves N_series = 27 unchanged (`results/sensitivity_b_eta0.json`), but **equal N does not prove candidate identity:** `global_series()` does not use b (Jaccard = 1.0), and upstream `identify_clusters()` at b = 0.911 was **not** re-run (~9.8% label mismatch, `results/sensitivity_b0911_series_overlap.json`). Spatial Ogata MLE — future work; WLS in Appendix B is a reproducibility control only. The 142 sliding-window candidates are the dominant source of detector liberalness.

- **Paleoseismic and historical data** (~1% of catalog; 47 NOAA records pre-1900, p = 0.46) — **not significant**; not used for significance claims (see §2).
- **η parameters:** b = 1.0, df = 1.6 — BP (2004) convention; catalog b = 0.911 for Mc/completeness and MC null only; **b = 1.0 vs 0.911 → N = 27** (`results/sensitivity_b_eta0.json`); upstream η₀/clusters at b = 0.911 **not re-run** (GK/ZBZ path); N_obs via `global_series()` unaffected.
- **η₀:** affects GK/ZBZ `identify_clusters()`, **not** N_obs = `global_series()`; KDE at M≥6.5 **not verified**; ±20% — `not_applied`, future work (`pipeline_v2`).
- **ETAS null:** temporal MLE primary (`calibrate_etas_mle.py`); WLS — **Appendix B**.
- **Global-series gate:** mean pairwise GC **> 1500 km** (primary); Flinn–Engdahl counts diagnostic only (legacy ≥3 FE zones gave the same N=27 on the modern window).
- **Heuristic metric with tectonic hint:** **98%** of pairs use 1.5× GC fallback — **failed hypothesis test**, not a global-analysis improvement; **removed from primary pipeline** (great-circle only).
- **Detector liberal** — 142 windows before merge; see §5.7.
- **No physical mechanism established** — η metric is correlational; ΔCFS/dynamic stress — **future work only**.
- **Parameter sensitivity** (`results/sensitivity_eta_windows_gc.json`, `results/sensitivity_b_eta0.json`): GC 1000/1500/2000 km → N = 27; windows 1/2/5/10 yr → 53/27/11/6; b = 1.0 vs 0.911 in η — see `sensitivity_b_eta0.json`; η₀ **not applied** in `global_series()`.
- **Declustering:** N = 27 stable under GK/ZBZ/none at fixed gates; 24 vs 1 removed — **principally different** mainshock sets for cluster analysis.

Additionally: **GK is primary** for inference, ZBZ sensitivity-only; post-hoc BH on N = 47 (§3.8) — not a discovery claim; quality_score < 0.7 before 1960 limits early-instrumental interpretation.

### 5.7 Detector liberalism

The global-series search is **liberal by construction**:

1. **Sliding windows** — three sizes (1, 2, and 5 yr; 1-yr step) over the η NN forest yield **142 cluster candidates** before merging overlapping groups (`global_series()`).
2. **Series criteria** — N ≥ 4, M ≥ 6.5, mean pairwise GC > 1500 km — relatively permissive at global scale.
3. **Primary temporal MLE ETAS null** — p_ETAS = 1.0, mean = 27: detector consistent with calibrated null; **not** excess series.
4. **Parameter sensitivity** — consolidated table §4.4: GC 1000/1500/2000 → 27; windows 1/2/5/10 → 53/27/11/6; b 1.0/0.911 → 27 (Jaccard = 1.0); GK/ZBZ/none → 27; strict N ≥ 8 → 27; η₀ not_applied.

**Conclusion:** 47 merged candidates reflect liberal exploratory search; no anomalous temporal clustering beyond catalog-calibrated ETAS; spatial linkage among dispersed events remains open.

---

## 6. Conclusions

1. **No anomalous temporal clustering** beyond catalog-calibrated ETAS (N_obs = 27, mean = 27.0, p_ETAS = 1.0) in 2-yr detector windows.
2. **Spatial linkage not tested:** temporal-only ETAS; dispersed candidates (mean GC > 1500 km) lack validated physical mechanism; spatial null remains open.
3. **Permutation** p = 0.0001 — rejects Poisson times only; **not** proof of global chains.
4. **Primary ETAS-null** (temporal MLE): see §5.3 table.

Additionally: tectonic heuristic removed from primary pipeline; ΔCFS — future work.

Additionally: the heuristic metric with tectonic hint **does not improve** global analysis (98% GC fallback); tectonic heuristic **removed from primary pipeline**; **ΔCFS/dynamic stress — future work**; causal chains **not** established.

**Future work:** full ETAS MLE; ZBZ-primary declustering re-run; tightening **search space** (windows, η₀); ΔCFS/dynamic stress (S170, S047, S095). External DOI ([Zenodo](https://en.wikipedia.org/wiki/Zenodo)) deferred — GitHub only.

---

## Appendix A. Pre-1900 NOAA records

**47** fragmentary paleoseismic/historical M≥6.5 records from NOAA NGDC are retained in `data/processed/unified_catalog_full.csv` for provenance. **Not removed from CSV**; a separate pipeline re-run excluding them **was not performed**.

These 47 events are **excluded from the primary detector pipeline and ETAS calibration window**: the canonical pipeline (`pipeline_v2.py`) and ETAS fit (`calibrate_etas.py`) use the modern catalog **1973–2026 only** (*N* = 2,041). Epoch-stratified counts in §4.1 include pre-1900 descriptively via `run_full_historical_analysis.py` but do not enter primary significance claims.

- **quality_score:** 0.30–0.60 (metadata, not an inclusion filter).
- **Detector:** 5 algorithmic candidates on this epoch; permutation p = 0.46 — **not statistically significant**.
- **Primary significance path:** detector + ETAS + permutation claims — **1900–2026** (descriptive) and **1973–2026** (primary); pre-1900 is **outside** primary inference.

---

## Appendix B. Catalog-matched WLS negative control (reproducibility)

**Reproducibility demonstration only — not used for hypothesis testing.** Catalog-matched WLS (`results/etas_calibration.json`: μ ≈ 0.103, K ≈ 0.495) yields mean = 27.0, pETAS = 1.0 (n = 1000; multiseed stable). The fitted **K ≈ 0.495 is a catalog-WLS artifact** (detector--calibration coupling on 24 GK aftershocks); **invalid for inference**. Illustrates detector--calibration coupling on the same catalog; **not** the primary null.

| Component | Method |
|-----------|--------|
| μ | GK mainshocks / T (closed form) |
| c, p | Omori MLE, Nelder--Mead on 24 delays |
| K, α | WLS (`numpy.linalg.lstsq`) on the same 24 GK aftershocks |

---

## Data and Code Availability

Data and code: [github.com/marshalkin-ux/paleoseismic-clustering](https://github.com/marshalkin-ux/paleoseismic-clustering) (commit hash recorded at release). Analysis catalog: `data/processed/unified_catalog_full.csv` (4,418 rows; **4,267** unique M≥6.5 after dedup). Interactive presentation: [marshalkin-ux.github.io/paleoseismic-clustering](https://marshalkin-ux.github.io/paleoseismic-clustering/). Artifact paths: [docs/data_availability.md](https://github.com/marshalkin-ux/paleoseismic-clustering/blob/main/docs/data_availability.md).

---

## References

1. Baiesi M., Paczuski M. (2004). Scale-free networks of earthquakes and aftershocks. *Phys. Rev. E*, 69, 066106. doi:10.1103/PhysRevE.69.066106
2. Zaliapin I. et al. (2008). Clustering analysis of seismicity and aftershock identification. *Phys. Rev. Lett.*, 101, 018501.
3. Zaliapin I., Ben-Zion Y. (2013). Earthquake clusters in southern California I. *J. Geophys. Res.*, 118, 2847–2864.
4. Bird P. (2003). An updated digital model of plate boundaries. *Geochem. Geophys. Geosyst.*, 4(3), 1027.
5. Hill D.P. et al. (1993). Seismicity remotely triggered by the magnitude 7.3 Landers earthquake. *Science*, 260, 1617–1623.
6. Brodsky E.E., Prejean S.G. (2006). New constraints on mechanisms of remotely triggered seismicity. *J. Geophys. Res.*, 111, B06312.
7. Pollitz F.F. et al. (1998). Viscosity of oceanic asthenosphere inferred from remote triggering. *Science*, 280, 1245–1249.
8. King G.C.P. et al. (1994). Static stress changes and the triggering of earthquakes. *BSSA*, 84, 935–953.
9. Stein R.S. (1999). The role of stress transfer in earthquake occurrence. *Nature*, 402, 605–609.
10. Michael A.J. (2011). Random variability explains apparent global clustering of large earthquakes. *Geophys. Res. Lett.*, 38, L21301.
11. Shearer P.M., Stark P.B. (2012). Global risk of big earthquakes has not recently increased. *PNAS*, 109(3), 717–721.
12. Ogata Y. (1988). Statistical models for earthquake occurrences and residual analysis. *J. Amer. Stat. Assoc.*, 83, 9–27.
13. Benjamini Y., Hochberg Y. (1995). Controlling the false discovery rate. *J. Roy. Stat. Soc. B*, 57(1), 289–300.
14. Gardner J.K., Knopoff L. (1974). Is the sequence of earthquakes in Southern California Poissonian? *BSSA*, 64, 1363–1367.
15. Helmstetter A., Sornette D. (2003). Importance of direct and indirect triggered seismicity in the ETAS model. *J. Geophys. Res.*, 108, 2457.
16. Woessner J., Wiemer S. (2005). Assessing the quality of earthquake catalogues. *BSSA*, 95, 684–698.
16. Young J.B. et al. (1996). The Flinn–Engdahl regionalization scheme: the 1995 revision. *Phys. Earth Planet. Int.*, 96, 223–297.

---

## Acknowledgments

The author acknowledges USGS, NOAA NGDC, and the ISC for maintaining open seismic catalogs. This work received no targeted funding.

**Corresponding author:** Yaroslav Marshalkin, marshalkin@gmail.com
