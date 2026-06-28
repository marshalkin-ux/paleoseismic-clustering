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

We analyze an **analysis catalog of 4,267 unique M≥6.5 events**[^catalog-n] (modern window 1973–2026: 2,041 events); historical NOAA records (*n*=47)[^pre1900] are descriptive only. A Baiesi–Paczuski η detector with **great-circle distance** yields **27 algorithmic candidates** in the modern window. **Catalog-calibrated temporal ETAS** (GK mainshocks, 1973–2026): mean = 27.0, **p_ETAS = 1.0** — N_obs is consistent with the **in-sample temporal null**. Under the temporal ETAS model used, results are **consistent with the in-sample calibrated null**; the spatial component was not modeled, so questions of long-range spatial linkage remain open. **Limitation:** spatial component not modeled (§5).

[^catalog-n]: Canonical analysis N: **4,267** unique M≥6.5 after deduplication (±30 days, ≤50 km; ISC > USGS > NOAA; cf. Waldhauser & Schaff, 2008). **4,418** saved CSV rows include ~151 NOAA M<6.5 rows (provenance only).
[^pre1900]: 47 pre-1900 NOAA records retained in CSV for provenance; excluded from primary detector and ETAS calibration window (1973–2026).

**Keywords:** global seismicity; seismic series; earthquake clustering; Baiesi–Paczuski metric; ETAS validation; paleoseismology; Flinn–Engdahl

> **Terminology.** *Detector candidate* — algorithmic output (N≥4, M≥6.5, mean pairwise GC >1500 km, merged from sliding windows). *Series* in tables denotes such a candidate, **not** a validated physical chain. *Validated global chain* would require a physical mechanism and confirmation beyond the primary calibrated ETAS null; none established.

---

## 1. Introduction

Large earthquakes are not independent in time. Michael (2011) tested whether global M≥7 clustering in 1995–2011 exceeds Poisson rate fluctuations. Shearer & Stark (2012) tested whether global M≥7 and M≥8 rates increased after the 2004 Sumatra earthquake. Both found no anomalous global clustering beyond standard null models, but neither tested multi-regional η-linkage structure at M≥6.5 with catalog-calibrated ETAS validation.

**Objective.** Test whether physically meaningful multi-regional “global series” exist in the M≥6.5 catalog, with **primary inference on the modern window (1973–2026)**.

**Scope.** We extend prior global rate tests with a complementary Baiesi–Paczuski η detector and catalog-calibrated temporal ETAS null (§3.7). Conclusions are limited to temporal clustering in detector windows; spatial linkage requires future spatial ETAS (Ogata, 1998).

**Contribution.** This work provides a **reproducible** global M≥6.5 pipeline under explicit **falsification** framing and **bounds of inference**: primary ETAS uses **in-sample** calibration on 1973–2026 GK mainshocks with the **same** detector; spatial long-range linkage is **not** tested. The value is methodology plus honest null-result bounds — **not** a discovery claim. We do **not** claim to have disproved global series as a physical phenomenon; we bound what the implemented tests can establish.

### 1.1 Research question and testable hypotheses

**Research question (RQ):** Do physically meaningful multi-regional global series exist in the M ≥ 6.5 catalog (primary window 1973–2026)?

**Scope.** The **primary ETAS test** addresses **temporal** excess clustering in 2-yr detector windows only; it does **not** apply a spatial Ogata (1998) kernel and therefore does **not** test whether geographically dispersed candidates (mean GC > 1500 km) form a **physically linked** global series. That spatial linkage question requires spatial ETAS calibration (future work). We retain the title's spatiotemporal framing for the detector and η-metric, but conclusions are limited accordingly (§5.6).

Four distinct statistical targets must not be conflated (table below; see also §3.8).

| Test / hypothesis | H₀ (null) | H₁ (alternative) | Statistic | Result (modern) |
|-------------------|-----------|------------------|-----------|-----------------|
| **(a) Permutation** | Event times **independent** (Poisson process, fixed coordinates) | Times **dependent** (clustering) | mean log₁₀(η_NN); n = 10,000 | **Reject H₀:** p = 0.0001 (1/10,001) |
| **(b) ETAS-null (primary MLE)** | N_series ≤ **catalog-calibrated** temporal ETAS expectation (GK mainshocks) | N_series **exceeds** calibrated ETAS | series count in 1000 synthetic catalogs | **Do not reject H₀:** p_ETAS = 1.0; N_obs = 27 = mean = 27.0 |
| **(c) Global series** | **No** physically meaningful multi-regional series (no mechanism; liberal detector) | Teleseismic chains explainable by physics | detector + mechanism + null tests | **Not tested by temporal-only ETAS**; detector candidates lack validated physical mechanism; spatial null open |
| **(d) WLS coupling illustration**[^wls] | Detector--calibration artifact on same catalog | — | Appendix B only | **Not** primary null |

[^wls]: Catalog-matched WLS excluded from primary pipeline; coupling illustration only — see `paper/supplementary.md` §S2.

Permutation vs ETAS nuance — consolidated in Results (§4.1).

---

## 2. Data

### 2.1 Catalog compilation

**Magnitude notation.** Catalog thresholds and detector gates use **M ≥ 6.5** (USGS ComCat, predominantly M_w); individual events are cited with catalog type where relevant (e.g. M_w 7.3).

| Source | Period | Role |
|--------|--------|------|
| USGS ComCat | 1900–2026 | Primary instrumental catalog |
| ISC Bulletin | 1900–2023 | Relocated hypocenters for verification |
| NOAA NGDC | pre-1900 | Historical/paleoseismic records (47 events)[^pre1900] |

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

**Final analysis catalog:** 4,267 unique M≥6.5 events (4,418 CSV rows = raw merged file, not analysis N). **Primary analysis set:** events **1900–2026** (4,218); **47 pre-1900 records** stay in CSV (provenance) but are **excluded from the primary detector pipeline and ETAS calibration window** (1973–2026 only)[^pre1900].

| Epoch | Events M≥6.5 | Period |
|-------|---------------|--------|
| Early instrumental | 2,179 | 1900–1972 |
| Modern | 2,041 | 1973–2026 |
| Pre-1900 (provenance) | 47 | descriptive only |

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
5. **Detector gate (sole mandatory criteria):** N ≥ 4, M ≥ 6.5, **mean pairwise GC > 1500 km** (`results/clustering_gc1500.json`). Mean pairwise GC is **weaker** than requiring every pair > 1500 km — acknowledged limitation.
6. **Flinn–Engdahl zone count — diagnostic/reporting only**, not an admission criterion (legacy ≥3 FE threshold gave the same N = 27 on the modern window).

---

## 3. Methods

Unified pipeline (see §3.3 for detector algorithm): **Data** → **Deduplication** (±30 d, ≤50 km) → **η metric** → **GK declustering** (primary) → **series detection** (GC >1500 km) → **statistical tests** (permutation, ETAS, FDR).

### 3.1 Data and deduplication

Catalog sources and merge reconciliation are in §2.1. Duplicates merged at ±30 days and ≤50 km (cf. Waldhauser & Schaff, 2008); ISC > USGS > NOAA priority. **Analysis catalog: 4,267** unique M≥6.5 (4,418 CSV rows = provenance only).

### 3.2 Tectonic distance heuristic (excluded)

The Bird (2003) tectonic-path heuristic is **excluded from the primary pipeline**; no synthetic benchmark against Bird geometry in this work (`paper/supplementary.md` §S1).

### 3.3 η connectivity metric

Following Baiesi & Paczuski (2004) and Zaliapin et al. (2008):

**ηij = tij · rij^1.6 · 10^(−b·mi)**

| Component | Symbol | Physical meaning |
|-----------|--------|------------------|
| Time | tij (yr) | Penalty for large temporal separation |
| Distance | rij^1.6 (km) | Great-circle separation (primary pipeline) |
| Magnitude | 10^(−b·mi) | Weighting by parent-event magnitude mi |

Here df = 1.6 (fractal dimension; Baiesi & Paczuski, 2004) and **b = 1.0** (code default `B_DEFAULT`; parent magnitude mi only—no erroneous bi in the exponent). Smaller η indicates tighter spatiotemporal coupling.

*Note:* b = 1.0 and df = 1.6 follow Baiesi & Paczuski (2004) for cross-study η comparability — **deliberate convention**, not catalog-calibrated. At fixed detector gates, b = 0.911 leaves N_series = 27 (`results/sensitivity_b_eta0.json`); upstream `identify_clusters()` at b = 0.911 was **not** re-run.

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
| 7 | ETAS null | Temporal MLE primary (§3.7) |
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

GK applies conservative local window rules; ZBZ classifies only events with exceptionally low η to a predecessor. **Quantitative sensitivity** (`results/sensitivity_declustering.json`): GK, ZBZ, and no declustering all yield **N = 27** at fixed gates — because `global_series()` gates (mean GC > 1500 km, N ≥ 4, merge) dominate; declustering shifts upstream labels, not series count in this pipeline (**liberal-detector red flag**).

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

**Primary inference** uses catalog-calibrated temporal Ogata (1988) MLE on GK mainshocks (`scripts/calibrate_etas_mle.py`, `results/etas_mle_calibration.json`): μ ≈ 0.097, K ≈ 10⁻⁴, α ≈ 0.25, c = 0.001 day, p ≈ 1.91. Validation: `scripts/run_etas_validation.py` → `results/etas_validation.json`.

**In-sample disclaimer.** p_ETAS = 1.0 reflects **in-sample** calibration on 1973–2026 with the **same** detector — not independent out-of-sample validation. We report consistency with the **in-sample temporal null**, not proof of no anomalies. ETAS is a triggering model fit on GK-**declustered** mainshocks — acknowledged model mismatch. Complementary hold-out: train 1973–2000, validate 2001–2026 (`scripts/calibrate_etas_holdout.py` → `results/etas_holdout_validation.json`).

Catalog-matched WLS is **excluded from the primary pipeline** (coupling illustration only; `paper/supplementary.md` §S2). Spatial Ogata (1998) MLE — future work (`docs/future_work_etas_mle.md`).

Multi-seed ETAS (MLE primary): seeds 42–51, n = 1000 catalogs/seed (`scripts/run_etas_multiseed.py`, `results/etas_multiseed.json`).

### 3.8 Statistical validation

| Test | Null hypothesis | Role |
|------|-----------------|------|
| **ETAS MLE (primary)** | N_obs consistent with calibrated ETAS | **Primary** — full numbers in §4.1 |
| **Permutation** (n = 10,000) | Poissonian event times | Secondary — p cross-ref §4.1 only |
| **Benjamini–Hochberg** | — | Post-hoc on 47 merged candidates; not a discovery claim |

Post-hoc Benjamini–Hochberg on **N = 47** merged-series p-values (`results/fdr_correction_results.csv`): **45/47** at q = 0.05. Window-level BH on 142 overlapping tests is **not** a discovery procedure (`results/fdr_windows.json`).

**Verified from code.** `results/analysis_full_historical.json`, `results/montecarlo_full.json`, `results/etas_validation.json`, `results/sensitivity_declustering.json`.

---

## 4. Results

### 4.1 Primary counts (modern window, 1973–2026)

**Canonical catalog.** Merged CSV: **4,418 rows** → **4,267 unique M≥6.5** after deduplication (±30 days, ≤50 km); **~151 NOAA M<6.5 rows** excluded from clustering. **Modern window: 2,041 events.** GK declustering: 2,017 mainshocks (24 aftershocks removed).

| Quantity | Value |
|----------|------:|
| N_series (merged, all epochs) | 47 |
| N_series (modern) | **27** |
| Window candidates before merge | 142 |
| Permutation p (Methods §3.8) | 0.0001 (1/10,001); z = −6.17 |
| **Primary ETAS MLE** (n = 1000, seed = 42) | **N_obs = 27**, **mean = 27.0**, **p_ETAS = 1.0** (in-sample) |
| **Hold-out ETAS** (train 1973–2000, hold-out 2001–2026) | **N_obs = 13**, mean = 13.0, **p = 1.0** |
| ETAS parameters (MLE, full window) | μ ≈ 0.097, K ≈ 10⁻⁴, α ≈ 0.25 |

> **Permutation vs ETAS — different hypotheses (not in abstract).** The permutation test rejects **Poisson event times** (p = 0.0001) — expected with aftershocks (Ogata, 1988). **Primary in-sample ETAS MLE** gives **p_ETAS = 1.0**: N_obs = 27 is **consistent with the in-sample temporal null** — not proof of no anomalies. Hold-out (2001–2026): N_obs = 13, mean = 13.0, p = 1.0. Neither test confirms physically linked global chains; spatial linkage was not modeled.

**Declustering sensitivity** (`results/sensitivity_declustering.json`): GK, ZBZ, and none all yield **N = 27** at fixed gates (2 yr, mean GC > 1500 km, N ≥ 4). `global_series()` gates dominate; declustering affects upstream labels, not series count — a **liberal-detector red flag**, not proof that declustering is immaterial in general.

| Method | Removed | N_series |
|--------|--------:|---------:|
| Gardner–Knopoff (primary) | 24 | 27 |
| Zaliapin–Ben-Zion | 1 | 27 |
| None | 0 | 27 |

**Other epochs (descriptive).** Early instrumental (1900–1972): 15 candidates, p = 0.007 (quality_score < 0.7 before 1960). Pre-1900[^pre1900]: 5 candidates, p = 0.46 — not used for significance claims.

### 4.2 Top-5 detector candidates (illustrative)

> **Table 1 — Raw detector candidates, NOT validated series.** Entries are algorithmic outputs from sliding windows; **illustrative only** — not ETAS-validated physical chains. Do not interpret as discoveries.

| Series | N | Regions | Mmax | Period | lat° | lon° |
|--------|--:|--------:|-----:|--------|------|------|
| 1905–1910 | 193 | 43 | 8.8 | 1905–1910 | −60…72 | −180…180 |
| S047 | 53 | 5 | 8.0 | 1982–2024 | −21.5…18.9 | −175.5…155.2 |
| S170 | 46 | 12 | 9.1 | 2002–2023 | −14.3…33.8 | −113.1…167.3 |
| S095 | 25 | 4 | 7.9 | 1989–2017 | −8.1…16.5 | 120.4…146.4 |
| S116 | 22 | 5 | 8.2 | 1993–2021 | −31.7…10.8 | −179.5…179.4 |

**S170** (2004 Sumatra M 9.1) is a descriptive modern example, not a validated physical series.

### 4.3 Spatial–temporal patterns

Elevated detector-candidate frequency in 1952–1965 and 2002–2016; spatial concentration along the circum-Pacific belt.

### 4.4 Parameter sensitivity (modern window)

| Parameter | Setting | N_series |
|-----------|---------|--------:|
| GC gate | 1000 / 1500 / 2000 km | 27 / 27 / 27 |
| Window | 1 / 2 / 5 / 10 yr | 53 / **27** / 11 / 6 |
| b in η | 1.0 / 0.911 | 27 / 27 |
| Declustering | GK / ZBZ / none | 27 / 27 / 27 |
| min_events | 5 / 6 / 8 | 27 / 27 / 27 |

Sources: `sensitivity_eta_windows_gc.json`, `sensitivity_b_eta0.json`, `sensitivity_declustering.json`.

---

## 5. Discussion and conclusions

- **Temporal ETAS (primary, in-sample):** N_obs = 27 is **consistent with the in-sample temporal null** (p_ETAS = 1.0); hold-out 2001–2026: N_obs = 13, p = 1.0. Spatial linkage **not tested** (Ogata, 1998 — future work).
- **Permutation:** Rejects Poisson event times only — **not** proof of teleseismic/global chains (§4.1).
- **Prior work:** Compatible with Michael (2011) and Shearer & Stark (2012).

**Limitations (§5.6).** Temporal ETAS only; in-sample calibration; GK/ETAS model mismatch; mean GC gate weaker than all-pairs; Bird excluded (no synthetic benchmark); FDR post-hoc on 47 merged series only. See `docs/future_work_etas_mle.md` for spatial Ogata MLE and synthetic benchmarks.

---

## Appendix A. Pre-1900 NOAA records

**47** fragmentary paleoseismic/historical M≥6.5 records from NOAA NGDC are retained in `data/processed/unified_catalog_full.csv` for provenance. **Not removed from CSV**; a separate pipeline re-run excluding them **was not performed**.

These 47 events are **excluded from the primary detector pipeline and ETAS calibration window**: the canonical pipeline (`pipeline_v2.py`) and ETAS fit (`calibrate_etas.py`) use the modern catalog **1973–2026 only** (*N* = 2,041). Epoch-stratified counts in §4.1 include pre-1900 descriptively via `run_full_historical_analysis.py` but do not enter primary significance claims.

- **quality_score:** 0.30–0.60 (metadata, not an inclusion filter).
- **Detector:** 5 algorithmic candidates on this epoch; permutation p = 0.46 — **not statistically significant**.
- **Primary significance path:** detector + ETAS + permutation claims — **1900–2026** (descriptive) and **1973–2026** (primary); pre-1900 is **outside** primary inference.

---

## Appendix B. WLS coupling illustration

Excluded from primary pipeline. Full specification: `paper/supplementary.md` §S2 and `results/etas_calibration.json`.

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
