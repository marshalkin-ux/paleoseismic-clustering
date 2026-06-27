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

We test the hypothesis of physically meaningful **multi-regional global seismic series** in a merged catalog of **4,267 unique M≥6.5 events** (4,418 CSV rows; ~151 NOAA M<6.5 rows retained for provenance, excluded from clustering) using the Baiesi–Paczuski metric η with a **heuristic metric with tectonic hint** (Bird 2003 graph). **Primary result — negative (null/falsification):** on the modern window (1973–2026, 2,041 events), catalog-calibrated [ETAS](https://en.wikipedia.org/wiki/Epidemic-type_aftershock_sequence) without long-range links (>500 km) reproduces **N_obs = 27** detector episodes (**mean = 27.0**, **pETAS = 1.0**, FPR = 1000/1000, n = 1000) — **no excess “global” structure beyond ETAS-like local clustering**. The [permutation test](https://en.wikipedia.org/wiki/Permutation_test) (n = 10,000, **p = 0.0001 (1/10,001 permutations)**[^mc-p], z = −6.17) rejects a **global temporal Poisson null** — expected for catalogs with aftershocks/local clustering; **this is not a test of the multi-regional global-series hypothesis** and does **not** prove teleseismic triggering. The detector yields **47 algorithmic candidates** (142 window candidates before merge; 27 modern). We tested an alternative to Euclidean distance (Bird 2003 graph): in **98%** of pairs the implementation falls back to 1.5× great-circle distance — effectively scaled Euclidean; **no improvement for global analysis** (failed hypothesis test). **ΔCFS/dynamic stress — future work only**; “series” are algorithmic constructs, not proven triggering chains.

[^mc-p]: Discrete permutation test with n = 10,000: p = (k+1)/(n+1) where k is the count of null replicates at least as extreme as observed. Here k = 0, so p = 1/10,001 ≈ 0.0001. We report **p = 0.0001 (1/10,001 permutations)**; equivalently p < 0.001.

**Keywords:** global seismicity; seismic series; earthquake clustering; heuristic metric with tectonic hint; Baiesi–Paczuski metric; ETAS validation; Monte Carlo; paleoseismology; Flinn–Engdahl

---

## 1. Introduction

Large earthquakes do not occur as independent [Poisson](https://en.wikipedia.org/wiki/Poisson_point_process) events. Following the 1992 Landers earthquake (Mw 7.3), Hill et al. (1993) documented remotely triggered seismicity at distances exceeding 1,000 km. Brodsky & Prejean (2006) showed that surface waves can initiate swarms in volcanic systems thousands of kilometres away. After the 2004 Sumatra–Andaman earthquake (Mw 9.1), elevated activity was reported in distant regions; possible mechanisms were discussed earlier (Pollitz et al., 1998; Freed & Lin, 2001) — **correlation within series S170 does not establish causality**.

However, the systematic nature of such correlations remains debated. Michael (2011) tested whether global M≥7 clustering in 1995–2011 exceeds Poisson rate fluctuations. Shearer & Stark (2012) tested whether global M≥7 and M≥8 rates increased after the 2004 Sumatra event. Kagan & Jackson (1999) confirmed elevated probability of paired events at short separation without resolving long-range links.

The [ETAS](https://en.wikipedia.org/wiki/Epidemic-type_aftershock_sequence) model (Ogata, 1988) reproduces regional aftershock clustering but does not encode inter-plate correlations. The [Baiesi–Paczuski](https://en.wikipedia.org/wiki/Earthquake_clustering) (2004) metric and Zaliapin–Ben-Zion extensions (2008, 2013) provide objective cluster detection but typically use Euclidean distance, ignoring lithospheric connectivity.

**Objective.** Test (and if warranted, **falsify**) the hypothesis that physically meaningful multi-regional “global series” exist, with **primary inference on the modern window (1973–2026)**, using complementary null tests (permutation vs ETAS) and explicit detector liberalness assessment.

**Scope.** We combine nearest-neighbor clustering with a heuristic metric with tectonic hint and ETAS null-model validation; this extends prior global rate tests (Michael 2011; Shearer & Stark 2012) with a complementary η-linkage statistic but does not supersede their conclusions.

---

## 2. Data

### 2.1 Catalog compilation

| Source | Period | Role |
|--------|--------|------|
| USGS ComCat | 1900–2026 | Primary instrumental catalog |
| ISC Bulletin | 1900–2023 | Relocated hypocenters for verification |
| NOAA NGDC | pre-1900 (47 events) | Historical and paleoseismic records |

Duplicate records were merged using ±30 days and ≤50 km spatial tolerance; source priority: ISC > USGS > NOAA. After deduplication, the catalog contains **4,267** unique M≥6.5 events (from **4,418** saved CSV rows). **151 sub-threshold rows** (NOAA, M<6.5 from the M≥6.0 fetch) **are retained in CSV for provenance but excluded from all clustering and series-detection steps**.

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

**Final catalog:** 4,267 events M≥6.5 (4,418 CSV records; M≥6.5 analysis set)

| Epoch | Events M≥6.5 | Period |
|-------|---------------|--------|
| Historical | 47 | pre-1900 (fragmentary paleoseismic records) |
| Early instrumental | 2,179 | 1900–1972 |
| Modern | 2,041 | 1973–2026 |

**47 pre-1900 NOAA records** are retained for provenance; epoch test yields p = 0.46 — **not used for significance claims** (see §4.1).

### 2.2 Catalog completeness

Maximum-curvature analysis yields Mc = 6.55. Maximum-likelihood b-value from 1,688 events above Mc:

**b = 0.911 ± 0.018**

The [Gutenberg–Richter](https://en.wikipedia.org/wiki/Gutenberg%E2%80%93Richter_law) relation is satisfied above Mc. **b-value consistency:** clustering η uses **b = 1.0** per the Baiesi & Paczuski (2004) convention for cross-catalog comparability; the Monte Carlo null and completeness analysis use the fitted **b = 0.911 ± 0.018**. This difference is intentional: η is a relative connectivity measure, not a rate forecast.

---

## 3. Methods

### 3.1 Heuristic metric with tectonic hint

We tested an alternative to Euclidean distance (Bird 2003 graph). In **98%** of pairs the implementation falls back to 1.5× great-circle distance — **effectively scaled Euclidean**; only **~2%** of boundary-proximal pairs use a Dijkstra path. **No improvement for global analysis** — failed hypothesis test.

We define rij as the shortest path between hypocenters along the global plate-boundary graph of Bird (2003), comprising 20 key segments (subduction zones, transform faults, mid-ocean ridges). Paths are computed with Dijkstra's algorithm (NetworkX). When either hypocenter lies more than 500 km from the nearest boundary node, or when no graph path exists between plate segments, we apply a penalty fallback:

**rij = 1.5 × rGC**

where rGC is the great-circle (Haversine) distance.

**Limitations and validation.** The 500 km boundary snap and 1.5× great-circle fallback are **approximations**, not verified against independent geodetic data. Intraplate pairs rely entirely on the GC penalty. A systematic audit (`scripts/analyze_tectonic_fallback.py`, `results/tectonic_fallback_analysis.json`, `figures/grl/fig07_tectonic_path_usage.png`) on **4987 random M≥6.5 pairs** from **500 sampled events** (1973+) shows **98.0% use the 1.5× GC fallback** and only **2.0% a real Dijkstra path** on the Bird (2003) graph. Fallback reasons: **4015** pairs exceed the 500 km boundary snap, **872** have no graph path, **100** use Dijkstra. Among Dijkstra pairs, **95** are materially different from the GC fallback (ratio tectonic/fallback > 1.5); examples include Japan (**FE31**, tectonic 365 km vs GC 10 km) and the Philippines (**FE35**, 495 km vs 42 km). **Reframing:** the tectonic metric adds lithospheric connectivity information only for **boundary-proximal pairs (~2%)**; for the vast majority of pairs it reduces to a fixed 1.5× GC penalty. The tectonic diagnostic (`figures/grl/fig05_tectonic_vs_euclidean.png`) yields **median Δlog₁₀η = +0.28**, consistent with GC-fallback dominance (1.6 log₁₀ 1.5 ≈ 0.28). This is a metric diagnostic, not a calibrated sensitivity gain.

**Sensitivity (planned, not yet run).** A full parameter sweep has not been conducted. Planned work:

| Parameter | Current value | Planned sweep |
|-----------|---------------|---------------|
| Boundary snap threshold | 500 km | 300 / 500 / 700 km |
| GC fallback multiplier | 1.5× | 1.2 / 1.5 / 2.0× |
| Bird graph resolution | 20 segments | 20 vs finer segmentation |

Until the sweep is complete, η-link conclusions apply to the baseline configuration (500 km, 1.5× GC, 20 segments).

### 3.2 Connectivity metric η

Following Baiesi & Paczuski (2004) and Zaliapin et al. (2008):

**ηij = tij · rij^1.6 · 10^(−b·mi)**

| Component | Symbol | Physical meaning |
|-----------|--------|------------------|
| Time | tij (yr) | Penalty for large temporal separation |
| Distance | rij^1.6 (km) | Penalty for large separation (heuristic with tectonic hint) |
| Magnitude | 10^(−b·mi) | Weighting by parent-event magnitude mi |

Here df = 1.6 (fractal dimension; Baiesi & Paczuski, 2004) and **b = 1.0** (code default `B_DEFAULT`; parent magnitude mi only—no erroneous bi in the exponent). Smaller η indicates tighter spatiotemporal coupling.

*Note:* b = 1.0 follows Baiesi & Paczuski (2004) for cross-study η comparability; the catalog empirical b = 0.911 ± 0.018 is used only in the Monte Carlo null and completeness analysis, not in the η formula.

**Units note.** η is a relative connectivity measure without absolute physical units; only ratios and log10(η) statistics are interpreted. The threshold η0 is determined empirically from the observed nearest-neighbor distribution, not from first principles.

### 3.3 Analysis pipeline

```
Raw catalogs (USGS / ISC / NOAA)
        ↓
   Dedup (±30 d, ≤50 km)
        ↓
   Exclude M<6.5 (~151 NOAA rows) → 4,267 unique M≥6.5
        ↓
 GK declustering (primary) → mainshocks for η NN forest
        ↓
 η NN forest (heuristic with tectonic hint, Bird 2003)
        ↓
 Sliding windows (1 / 2 / 5 yr)
        ↓
 Merge overlapping groups
        ↓
 Series criteria (N≥4, M≥6.5, ≥3 FE regions)
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

GK applies conservative local window rules; ZBZ classifies only events with exceptionally low η to a predecessor. The 23-event gap reflects **algorithm and parameter choice**, not conflicting physics. **GK is primary for all inference** (pipeline, ETAS calibration, reported counts). The ZBZ check shows **minimal additional removal** (1 event) — declustering is not a critical methodological fork. **If ZBZ were primary**, 23 GK-aftershocks would remain as mainshocks; these are short-range local pairs unlikely to enter multi-regional series (≥3 Flinn–Engdahl regions), so **N=27 modern series would likely change negligibly** — **not re-run** (`decluster_method='zaliapin'` exists in `pipeline_v2.py` but series count is untested).

### 3.4 Threshold η0, series detection, and ETAS parameters

1. **Declustering** via [Gardner–Knopoff](https://en.wikipedia.org/wiki/Aftershock) (1974) — mainshocks for NN search.
2. **Nearest-neighbor forest:** for each event j, parent i* = argmin ηij.
3. **Threshold η0:** automatic selection from the distribution of nearest-neighbor η values. Primary method: KDE valley detection between bimodal modes in log10(η) (Zaliapin & Ben-Zion, 2013). Default cluster cut when unspecified: η0 = 10^(median log10 η). The threshold is validated against a Poisson temporal-permutation null (Monte Carlo, n = 10,000).
4. **Global series criterion:** N ≥ 4 events; M ≥ 6.5; ≥ 3 [Flinn–Engdahl](https://en.wikipedia.org/wiki/Flinn%E2%80%93Engdahl_regions) regions.
5. **Sliding windows** (1, 2, 5 yr; 1-yr step); overlapping groups merged.

**ETAS null-model parameters (catalog-calibrated).** ETAS validation uses parameters estimated by minimal MLE on the **2,041**-event modern catalog (1973–2026, M≥6.5) after Gardner–Knopoff declustering (`scripts/calibrate_etas.py`, `results/etas_calibration.json`): **μ≈0.103, K≈0.495, α≈0.063, c≈10⁻⁴ d, p≈1.36** (see §3.5). Literature defaults (Helmstetter & Sornette, 2003) are retained for **comparison only**. Rejecting the ETAS null tests whether our series exceed a **catalog-calibrated** local-aftershock model without long-range links (>500 km). Multi-seed robustness: **10 seeds (42–51)**, n=1000 catalogs/seed (`scripts/run_etas_multiseed.py`, `results/etas_multiseed.json`).

### 3.5 Statistical validation

#### Multiple comparisons

Post-hoc demonstration of the [Benjamini–Hochberg](https://en.wikipedia.org/wiki/False_discovery_rate) procedure on **N = 47** merged-series p-values (after sliding windows 1/2/5 yr, merge, and series criteria N ≥ 4, M ≥ 6.5, ≥ 3 FE regions; see `results/fdr_correction_results.csv`): **45/47** at q = 0.05. This **does not** correct the 142 window candidates × search parameters and is **not** a discovery claim — detector sensitivity only (see §5.6).

**ETAS null model.** We generate synthetic catalogs with **catalog-calibrated** parameters (`results/etas_calibration.json`: μ≈0.103, K≈0.495, α≈0.063, c≈10⁻⁴ d, p≈1.36; GK+Omori MLE on 2,041 events). On the real modern catalog the algorithm finds **N_obs = 27** series.

**Single-seed run (seed = 42, n = 1000):** **1000/1000** catalogs contain ≥1 spurious series (**FPR = 1.0**); mean **27.0 ± 0.0** (max **27**). **pETAS = P(N_ETAS ≥ 27) = 1.0**.

**Multi-seed robustness (seeds 42, 43, 44, 45, 46, 47, 48, 49, 50, 51; n = 1000 catalogs/seed; `results/etas_multiseed.json`):**

| Seed | mean false series | σ | pETAS | FPR |
|------|------------------:|--:|------:|----:|
| 42 | 27.0 | 0.0 | 1.0 | 1.0 |
| 43 | 27.0 | 0.0 | 1.0 | 1.0 |
| 44 | 27.0 | 0.0 | 1.0 | 1.0 |
| 45 | 27.0 | 0.0 | 1.0 | 1.0 |
| 46 | 27.0 | 0.0 | 1.0 | 1.0 |
| 47 | 27.0 | 0.0 | 1.0 | 1.0 |
| 48 | 27.0 | 0.0 | 1.0 | 1.0 |
| 49 | 27.0 | 0.0 | 1.0 | 1.0 |
| 50 | 27.0 | 0.0 | 1.0 | 1.0 |
| 51 | 27.0 | 0.0 | 1.0 | 1.0 |

**Overall:** mean = **27.0**, σ = **0.0** across all seeds — perfect stability because calibrated ETAS generates catalogs with ~2,001 background events and local-only triggering (>500 km cutoff), matching the event rate and clustering scale of the real catalog; the detector then yields **exactly 27** spurious multi-regional series on every realization (see §5.6).

**Literature-default comparison only** (Helmstetter & Sornette 2003: μ=0.008, K=0.08; earlier exploratory runs with n=100 catalogs/seed): mean≈**15.5**, max=24, pETAS ≤ 0.001 — sensitive to parameter choice, **not** the primary null model.

| Test | Parameters | Result |
|------|------------|--------|
| Permutation ([Monte Carlo](https://en.wikipedia.org/wiki/Monte_Carlo_method)) | n = 10,000 | p = 0.0001 (1/10,001)[^mc-p], z = −6.17 (modern) |
| ETAS null model | μ≈0.103, K≈0.495; 1000 cat.; N_obs=27 | FPR = 1000/1000; mean 27.0; pETAS = 1.0 |
| Declustering (primary) | GK | 2,017/2,041 (24 aftersh.) |

**Verified from code.** Series counts and epoch p-values: `results/analysis_full_historical.json`. Monte Carlo (p, z): `results/montecarlo_full.json`. ETAS (FPR, p_ETAS): `results/etas_validation.json`. GK/ZBZ counts: `scripts/run_declustering_comparison.py`. Tectonic diagnostic (median Δlog₁₀η = +0.28): `scripts/generate_grl_figures.py::fig_tectonic_vs_euclidean`.

---

## 4. Results

### 4.1 Detector candidates (not “discovered series”)

**47 algorithmic candidates** after merge (142 window candidates before merging). These are **detector outputs** (see §5.6), not validated physical episodes:

| Epoch | N series | Events | p-value | z-score |
|-------|----------|--------|---------|---------|
| Modern (1973–2026) | 27 | 2,041 | 0.0001 (1/10,001) | −6.17 |
| Early instrumental (1900–1972) | 15 | 2,179 | 0.007 | −2.43 |
| Historical (pre-1900) | 5 | 47 | 0.46 | — |

**Modern period.** Twenty-seven candidates; permutation p = 0.0001 (1/10,001) rejects a **temporal Poisson null**, but **ETAS-null** (mean = 27, pETAS = 1.0) shows this is **indistinguishable** from locally clustered synthetic catalogs.

**Early instrumental period.** Fifteen series reach p = 0.007, but this result must be interpreted cautiously: most pre-1960 events have quality_score < 0.7, and catalog incompleteness inflates inter-event intervals, reducing detection power.

**Historical period:** five candidates; see §2 (47 NOAA records, p = 0.46 — not used for significance claims).

### 4.2 Top five multi-regional detector candidates

> **Disclaimer:** entries below are **detector candidates**, indistinguishable from ETAS-null noise; **do not interpret as physical series** or proven triggering chains.

| Series | N | Regions | Mmax | Period |
|--------|---|---------|------|--------|
| 1905–1910 | 193 | 43 | 8.8 | 1905–1910 |
| S047 | 53 | 5 | 8.0 | 1982–2024 |
| S170 | 46 | 12 | 9.1 | 2002–2023 |
| S095 | 25 | 4 | 7.9 | 1989–2017 |
| S116 | 22 | 5 | 8.2 | 1993–2021 |

The **1905–1910** episode (193 events, 43 regions) is the **largest candidate in the early instrumental window**; catalog completeness before ~1960 is poor (quality_score < 0.7) — **not** “largest series of all time.” **S170** is a modern-window detector candidate (12 Flinn–Engdahl regions, including 2004 Sumatra M 9.1); a descriptive example, not a validated physical series (Figures 1–2 in the repository).

### 4.3 Spatial–temporal distribution

Elevated series activity occurs in 1952–1965 and 2002–2016 (post-Sumatra period). Spatially, clusters concentrate along the circum-Pacific belt (Kamchatka, Kuril Islands, Japan, Tonga, Indonesia). The tectonic-vs-Euclidean diagnostic (§3.1) reports median Δlog₁₀η = +0.28 on random pairs; this reflects the 1.5× GC fallback for most samples, not a validated η₀ shift.

---

## 5. Discussion

### 5.1 Reconciling null models (permutation vs ETAS)

The two null tests **do not contradict** each other — they target **different hypotheses**:

| Test | Null hypothesis | Result | Interpretation |
|------|-----------------|--------|----------------|
| **Permutation** (n = 10,000) | Globally **Poissonian event times** with fixed coordinates | p = 0.0001 (1/10,001), z = −6.17 | Rejects temporal independence; expected with aftershocks/local clustering |
| **ETAS** (n = 1000, calibrated) | Detector **series count** does not exceed synthetic catalogs with **local** clustering only (>500 km cutoff) | mean = 27.0, pETAS = 1.0, FPR = 1000/1000 | **Does not** reject null: N_obs = 27 **indistinguishable** from ETAS-like local clustering |

**Explicit:** rejecting the Poisson permutation null **≠** evidence for teleseismic/global triggering.

Multiseed ETAS (seeds 42–51, n = 1000 catalogs/seed, calibrated parameters, `results/etas_multiseed.json`): **mean = 27.0** stable across all seeds; **FPR = 1.0**, **pETAS = 1.0** — N_obs = 27 indistinguishable from null.

| Seed | mean | σ | pETAS | FPR |
|------|-----:|--:|------:|----:|
| 42 | 27.0 | 0.0 | 1.0 | 1.0 |
| 43 | 27.0 | 0.0 | 1.0 | 1.0 |
| 44 | 27.0 | 0.0 | 1.0 | 1.0 |
| 45 | 27.0 | 0.0 | 1.0 | 1.0 |
| 46 | 27.0 | 0.0 | 1.0 | 1.0 |
| 47 | 27.0 | 0.0 | 1.0 | 1.0 |
| 48 | 27.0 | 0.0 | 1.0 | 1.0 |
| 49 | 27.0 | 0.0 | 1.0 | 1.0 |
| 50 | 27.0 | 0.0 | 1.0 | 1.0 |
| 51 | 27.0 | 0.0 | 1.0 | 1.0 |

### 5.2 Statistical sensitivity vs physical mechanism

**Established (null/falsification):** the hypothesis of **excess global structure** beyond ETAS-like local clustering is **not supported** (pETAS = 1.0). The permutation test detects deviation from a **global temporal Poisson** null — not from ETAS-null.

**Not established (physics):** η is correlative; **no physical mechanism** explains remote links in candidates. Preliminary Coulomb/dynamic stress tests for S170 **did not** reach triggering thresholds — **future work only**. Candidates are **algorithmic constructs**, not proven triggering chains.

**Early instrumental period (1900–1972).** Fifteen series reach p = 0.007 (z = −2.43), but quality_score < 0.7 before 1960 limits interpretation of individual episodes (including 1905–1910).

**Reconciliation with Michael (2011) and Shearer & Stark (2012).** Michael tested complementary Poisson **rate** nulls for global M≥7 clustering; Shearer & Stark tested whether post-2004 **event rates** increased. Our η-linkage test adds a **different statistic** (multi-regional nearest-neighbor structure) but **does not supersede** their conclusions about rates and short-window clustering models. The findings are complementary, not contradictory.

The tectonic diagnostic (§3.1; median Δlog₁₀η = +0.28) quantifies the GC-fallback penalty on random pairs; only **~2%** of audited boundary-proximal pairs use a real Dijkstra path (§3.1)—the metric adds limited value beyond Euclidean distance for most pairs.

### 5.3 Working hypotheses (future work, not claims)

Correlative η links **do not prove** any single mechanism. Possible (unverified) explanations for long-range coupling include:

- **Viscoelastic mantle coupling** — stress redistribution over months to years after major ruptures (Pollitz et al., 1998).
- **Dynamic triggering by surface waves** — short-lived activation at thousands of kilometres (Hill et al., 1993; Brodsky & Prejean, 2006).
- **Shared tectonic loading / stress redistribution** — secular loading without direct triggering (Freed & Lin, 2001).

Co-occurrence within a series may reflect any of these (or other) processes, or catalog artifacts.

### 5.6 Detector liberalism

The global-series search is **liberal by construction**:

1. **Sliding windows** — three sizes (1, 2, and 5 yr; 1-yr step) over the η NN forest yield **142 cluster candidates** before merging overlapping groups (`global_series()`).
2. **Series criteria** — N ≥ 4, M ≥ 6.5, ≥ 3 [Flinn–Engdahl](https://en.wikipedia.org/wiki/Flinn%E2%80%93Engdahl_regions) regions — relatively permissive at global scale.
3. **ETAS calibration** — on synthetic catalogs without long-range links (>500 km), the detector finds **mean = 27.0** “series” when **N_obs = 27** on the real modern window; **FPR = 1000/1000**, **pETAS = 1.0** (n = 1000, seed = 42). Multiseed (seeds 42–51): mean = 27.0, σ = 0.0, FPR = 1.0 stable (`results/etas_multiseed.json`).
4. **Threshold sensitivity** — min_events = 5, min_regions = 4 (and stricter) **do not reduce** N = 27 on the modern window (`results/clustering_sensitivity_strict.json`): liberalness lies in **search space** (142 windows), not small N.

**Conclusion:** 47 merged candidates and 27 on the modern window are **indistinguishable** from exploratory-search artifacts under ETAS-like local clustering — not validated physical episodes.

### 5.5 Limitations

**(1) Historical period:** see §2 (47 NOAA records, p = 0.46 — not used for significance claims).

**(2) ETAS.** Calibrated ETAS: mean = 27.0, pETAS = 1.0 — **negative result** for excess global structure. Detector liberalism — see §5.6.

**(3) Heuristic metric with tectonic hint:** 500 km / 1.5× GC approximations; **98%** of audited pairs use GC fallback (4987 pairs, §3.1); real Dijkstra paths for **~2%** only; failed hypothesis test.

**(4) Declustering asymmetry.** **GK is primary** for all inference; ZBZ (1 vs 24 dependent events) is sensitivity-only — different algorithms (window-based vs η-space clustering), not co-equal methods. Full-epoch `run_full_historical_analysis.py` does not pre-filter with GK; ZBZ-primary series count untested (likely negligible for N=27).

**(5) Multiple comparisons.** Post-hoc BH on N = 47 — see §3.5; not a discovery claim.

**(6) Causality:** series ≠ direct triggering; shared loading and mantle coupling are alternative explanations.

**(7) Catalog completeness.** Pre-1960 quality_score < 0.7 limits early-instrumental interpretation; Mc = 6.55 and b-value estimates apply to the instrumental subset.

---

## 6. Conclusions

Catalog-calibrated ETAS shows that the number of multi-regional clusters flagged by the detector (see §5.6) **does not exceed** what is expected from local aftershock activity alone. The hypothesis of physically meaningful global seismic series is **therefore not supported**. The permutation test rejects only a temporal Poisson null (p = 0.0001, 1/10,001) — **trivial** for earthquake catalogs with aftershocks; **not** a test of the multi-regional global-series hypothesis.

Additionally: the heuristic metric with tectonic hint **does not improve** global analysis (98% GC fallback); 47 detector candidates are **indistinguishable** from ETAS null (§5.6); **ΔCFS/dynamic stress — future work**; causal chains **not** established.

**Future work:** full ETAS MLE; ZBZ-primary declustering re-run; tightening **search space** (windows, η₀); ΔCFS/dynamic stress (S170, S047, S095). External DOI ([Zenodo](https://en.wikipedia.org/wiki/Zenodo)) deferred — GitHub only.

---

## Data and Code Availability

Data and code are openly available at the GitHub repository: [github.com/marshalkin-ux/paleoseismic-clustering](https://github.com/marshalkin-ux/paleoseismic-clustering). Interactive presentation: [marshalkin-ux.github.io/paleoseismic-clustering](https://marshalkin-ux.github.io/paleoseismic-clustering/). Analysis artifact paths are documented in [docs/data_availability.md](https://github.com/marshalkin-ux/paleoseismic-clustering/blob/main/docs/data_availability.md).

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
15. Woessner J., Wiemer S. (2005). Assessing the quality of earthquake catalogues. *BSSA*, 95, 684–698.
16. Young J.B. et al. (1996). The Flinn–Engdahl regionalization scheme: the 1995 revision. *Phys. Earth Planet. Int.*, 96, 223–297.

---

## Acknowledgments

The author acknowledges USGS, NOAA NGDC, and the ISC for maintaining open seismic catalogs. This work received no targeted funding.

**Corresponding author:** Yaroslav Marshalkin, marshalkin@gmail.com
