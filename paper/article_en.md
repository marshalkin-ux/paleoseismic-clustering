# Global Seismic Series: Statistical Analysis of Spatiotemporal Clustering in M≥6.5 Earthquake Catalogs, 1973–2026 CE

*Temporal ETAS null and hold-out validation — with extrapolation to the early instrumental period (1900–1972). Merged NOAA+USGS catalog; 4,267 M≥6.5 events (4,418 CSV rows).*

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

**Analysis catalog of 4,267 unique M≥6.5 events**[^catalog-n] (modern window 1973–2026: 2,041); Baiesi–Paczuski η detector (great-circle) yields **27 algorithmic candidates**. **Catalog-calibrated temporal ETAS:** **p_ETAS = 1.0** (consistent with in-sample null; full numbers — §4.1). Spatial component not modeled (§5). Pre-1900 NOAA records — Supplementary Material S3[^pre1900].

[^catalog-n]: Canonical analysis N: **4,267** unique M≥6.5 after deduplication (±30 days, ≤50 km; ISC > USGS > NOAA; cf. Waldhauser & Schaff, 2008). **4,418** saved CSV rows include ~151 NOAA M<6.5 rows (provenance only).
[^pre1900]: 47 pre-1900 NOAA records — `paper/supplementary.md` §S3; excluded from primary detector and ETAS calibration window (1973–2026).

**Keywords:** global seismicity; seismic series; earthquake clustering; Baiesi–Paczuski metric; ETAS validation; paleoseismology; Flinn–Engdahl

> **Terminology.** *Detector candidate* — algorithmic output (N≥4, M≥6.5, mean pairwise GC >1500 km, merged from sliding windows). *Series* in tables denotes such a candidate, **not** a validated physical chain. *Validated global chain* would require a physical mechanism and confirmation beyond the primary calibrated ETAS null; none established.

---

## 1. Introduction

Large earthquakes are not independent in time. Michael (2011) tested whether global M≥7 clustering in 1995–2011 exceeds Poisson rate fluctuations. Shearer & Stark (2012) tested whether global M≥7 and M≥8 rates increased after the 2004 Sumatra earthquake. Both found no anomalous global clustering beyond standard null models, but neither tested multi-regional η-linkage structure at M≥6.5 with catalog-calibrated ETAS validation.

**Objective.** Test whether physically meaningful multi-regional “global series” exist in the M≥6.5 catalog, with **primary inference on the modern window (1973–2026)**.

**Scope.** We analyze **detector candidates** with spatial gates (mean GC > 1500 km) but **validate only temporal excess** vs catalog-calibrated ETAS; the spatial linkage hypothesis is **not tested**. We extend prior global rate tests with a complementary Baiesi–Paczuski η detector and temporal ETAS null (§3.7). Conclusions are limited to temporal clustering in detector windows; spatial linkage requires future spatial ETAS (Ogata, 1998).

**Contribution.** This work provides a **reproducible** global M≥6.5 pipeline under explicit **falsification** framing and **bounds of inference**: primary ETAS uses **in-sample** calibration on 1973–2026 GK mainshocks with the **same** detector; spatial long-range linkage is **not** tested. The value is methodology plus honest null-result bounds — **not** a discovery claim. We do **not** claim to have disproved global series as a physical phenomenon; we bound what the implemented tests can establish.

### 1.1 Research question and testable hypotheses

**Research question (RQ):** Do physically meaningful multi-regional global series exist in the M ≥ 6.5 catalog (primary window 1973–2026)?

**Scope.** The **primary ETAS test** addresses **temporal** excess clustering in 2-yr detector windows only; it does **not** apply a spatial Ogata (1998) kernel and therefore does **not** test whether geographically dispersed candidates (mean GC > 1500 km) form a **physically linked** global series. That spatial linkage question requires spatial ETAS calibration (future work). We retain the title's spatiotemporal framing for the detector and η-metric, but conclusions are limited accordingly (§5.6).

Four distinct statistical targets must not be conflated (table below; see also §3.8).

| Test / hypothesis | H₀ (null) | H₁ (alternative) | Statistic | Result (modern) |
|-------------------|-----------|------------------|-----------|-----------------|
| **(a) Permutation** | Event times **independent** (Poisson process, fixed coordinates) | Times **dependent** (clustering) | mean log₁₀(η_NN); n = 10,000 | see **§4.1** |
| **(b) ETAS-null (primary MLE)** | N_series ≤ **catalog-calibrated** temporal ETAS expectation (GK mainshocks) | N_series **exceeds** calibrated ETAS | series count in 1000 synthetic catalogs | see **§4.1** |
| **(c) Global series** | **No** physically meaningful multi-regional series (no mechanism; liberal detector) | Teleseismic chains explainable by physics | detector + mechanism + null tests | **Not tested by temporal-only ETAS**; spatial null open |
| **(d) WLS coupling illustration**[^wls] | Detector--calibration artifact on same catalog | — | Supplementary S2 | **Not** primary null |

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
| Pre-1900 (provenance) | 47 | Supplementary S3 |

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

Pipeline: **Data** (§2) → **GK declustering** → **η NN forest** → **`global_series` detector** → **ETAS validation** (in-sample + hold-out).

### 3.1 Declustering (Gardner–Knopoff)

**Primary method:** Gardner–Knopoff (1974) on M≥6.5 (`GardnerKnopoffDeclustering` in `declustering.py`). `WINDOWS` table: M → (T[days], R[km]); linear interpolation; **magnitude-descending** iteration; aftershocks dt ∈ [0, T], foreshocks dt ∈ [−T/2, 0); haversine distance ≤ R. Mainshocks feed the η NN forest and series search.

Zaliapin–Ben-Zion declustering is **sensitivity only** (`run_declustering_sensitivity.py`), not a co-primary filter. Bird (2003) tectonic distance is excluded (`paper/supplementary.md` §S1).

### 3.2 η-metric (Baiesi–Paczuski)

Following Baiesi & Paczuski (2004) and Zaliapin et al. (2008):

**ηij = tij · rij^1.6 · 10^(−b·mi)**

| Component | Symbol | Physical meaning |
|-----------|--------|------------------|
| Time | tij (yr) | Penalty for large temporal separation |
| Distance | rij^1.6 (km) | Great-circle separation (primary pipeline) |
| Magnitude | 10^(−b·mi) | Weighting by parent-event magnitude mi |

**b = 1.0** and df = 1.6 follow Baiesi & Paczuski (2004) for cross-study comparability — deliberate convention, not catalog-calibrated. `find_nearest_neighbor` builds a causal NN forest (i* = argmin ηij). `identify_clusters()` applies η₀ from KDE valley of log₁₀(η) (Zaliapin & Ben-Zion, 2013); η₀ affects declustering labels only — **`global_series()` does not filter on η₀** (full counts in §4). Changing b in η re-runs upstream `identify_clusters()` labels only, not `global_series()` gates (full pipeline at b = 0.911 — §4.4, `sensitivity_b0911_full_pipeline.json`).

### 3.3 Detector (`global_series`, windows, merge, gates)

Implementation: `src/analysis/clustering.py`, `pipeline_v2.py`. **Output = algorithmic candidates**, not physical discoveries.

**`global_series`.** Greedy `used[]` mask; anchor loop; window [t_i, t_i+Δt); gates: min_events = 4, min_magnitude = 6.5, **mean pairwise GC > 1500 km**; accepted events marked used. Sliding windows **1, 2, 5 yr** (1-yr step); modern primary **Δt = 2 yr**. Overlapping window hits merged across epochs (`run_clustering_gc1500.py`). Flinn–Engdahl region count is diagnostic only.

```
GK mainshocks → η NN forest → windows 1/2/5 yr → merge → filter (N≥4, mean GC>1500 km) → candidates
```

Secondary tests: permutation (mean log₁₀ η_NN, n = 10,000); Benjamini–Hochberg post-hoc on merged candidates (not a discovery claim).

### 3.4 ETAS calibration (temporal MLE, in-sample disclaimer)

**Primary null:** catalog-calibrated temporal Ogata (1988) MLE on GK mainshocks 1973–2026 (`scripts/calibrate_etas_mle.py` → `results/etas_mle_calibration.json`). Validation: `scripts/run_etas_validation.py` → `results/etas_validation.json` (n = 1000 synthetics, seed = 42).

**In-sample disclaimer.** Calibration and validation use the **same** modern window and **same** detector — we report consistency with the **in-sample temporal null**, not proof of no anomalies. ETAS is fit on GK-**declustered** mainshocks — acknowledged model mismatch. Catalog-matched WLS excluded (`paper/supplementary.md` §S2). Spatial Ogata (1998) MLE — future work.

### 3.5 Hold-out validation (train 1973–2000, test 2001–2026)

Complements §3.4 (`scripts/calibrate_etas_holdout.py` → `results/etas_holdout_validation.json`):

| Item | Specification |
|------|---------------|
| Train window | 1973–2000 GK mainshocks (**1024** mainshocks) |
| Train MLE | μ ≈ 0.095, K ≈ 10⁻⁴, α = 0, c = 0.001 d, p ≈ 1.93 — **train only** |
| Hold-out catalog | 2001–2026, M ≥ 6.5 (**1010** events); parameters **fixed, no retraining** |
| Detector | Δt = 2 yr, mean GC > 1500 km, N ≥ 4 (same as primary) |
| Synthetics | n = 1000, seed = 42, max_total_events = 5000 |

Temporal Ogata (1988) MLE is fit **only** on train GK mainshocks 1973–2000; train-calibrated parameters are applied to the 2001–2026 hold-out **without re-fitting** (`scripts/calibrate_etas_holdout.py` → `results/etas_holdout_validation.json`: N_obs = 13, mean = 13.0, p_ETAS = 1.0). Partial **out-of-time** check — not spatial validation. Full validation numbers in §4.1.

---

## 4. Results

### 4.1 Primary counts (modern window, 1973–2026)

**Canonical catalog.** Merged CSV: **4,418 rows** → **4,267 unique M≥6.5** after deduplication (±30 days, ≤50 km); **~151 NOAA M<6.5 rows** excluded from clustering. **Modern window: 2,041 events.** GK declustering: 2,017 mainshocks (24 aftershocks removed).

| Quantity | Value |
|----------|------:|
| N_series (merged, all epochs) | 47 |
| N_series (modern) | **27** |
| Window candidates before merge | 142 |
| Permutation p (Methods §3.9) | 0.0001 (1/10,001); z = −6.17 |
| ETAS parameters (MLE, full window) | μ ≈ 0.097, K ≈ 10⁻⁴, α ≈ 0.25 |

**ETAS validation (canonical table):**

| Validation | Period | N_obs | mean | p_ETAS |
|------------|--------|------:|-----:|-------:|
| In-sample MLE | 1973–2026 | **27** | 27.0 | **1.0** |
| Hold-out | 2001–2026 | **13** | 13.0 | **1.0** |

Hold-out train: **1024** GK mainshocks (1973–2000); hold-out catalog **1010** events, span **25 yr** (`results/etas_holdout_validation.json`).

> **Permutation vs ETAS — different hypotheses (not in abstract).** Permutation rejects **Poisson event times** (p = 0.0001), not teleseismic chains. ETAS — consistency with catalog-calibrated temporal null (table above), not proof of no anomalies. Hold-out is a partial out-of-time check (§3.8), not spatial validation. Spatial linkage was not modeled.

**Declustering sensitivity** (`results/sensitivity_declustering.json`): GK, ZBZ, and none all yield **N = 27** at fixed gates (2 yr, mean GC > 1500 km, N ≥ 4). `global_series()` gates dominate; declustering affects upstream labels, not series count — a **liberal-detector red flag**, not proof that declustering is immaterial in general.

**Multiple testing (FDR).** The 27 modern series derive from a search over **142** sliding-window candidates (→ 47 merged across epochs). **FDR correction for this 142-window search was not applied** to the 27 modern count. A conservative Bonferroni threshold α/142 ≈ **0.00035** exceeds the global permutation p = **0.0001** (1/10,001), so the permutation rejection does not survive family-wise correction for all windows explored. Post-hoc Benjamini–Hochberg on **N = 47** merged-series p-values (45/47 at q = 0.05) is exploratory only and **does not** correct the 27 modern candidates for the window search — **not** a discovery claim (`results/fdr_windows.json`).

| Method | Removed | N_series |
|--------|--------:|---------:|
| Gardner–Knopoff (primary) | 24 | 27 |
| Zaliapin–Ben-Zion | 1 | 27 |
| None | 0 | 27 |

**N = 27 stability (Table 2).** At fixed gates (Δt = 2 yr, mean GC > 1500 km, N ≥ 4) the same event kernel survives the merge chain **142→47→27** under GK, ZBZ, and no declustering: Jaccard of **series event sets** vs GK baseline = 1.0, but Jaccard of **series membership** vs baseline = **0.32** for ZBZ/none (`series_stability_venn.json`) — declustering shifts upstream labels, not the series count. This reflects **liberal detector gates** and a shared event pool, **not** proof of a physically invariant “core 27.”

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

### 4.4 Parameter sensitivity and N=27 stability

| Parameter | Setting | N_series | Jaccard vs baseline† |
|-----------|---------|--------:|---------------------:|
| GC gate | 1000 / 1500 / 2000 km | 27 / 27 / 27 | 1.0 / 1.0 / 1.0 |
| Window Δt | 1 / 2 / 5 / 10 yr | 53 / **27** / 11 / 6 | 0 / 1.0 / 0 / 0 |
| Declustering | GK / ZBZ / none | 27 / 27 / 27 | 1.0 / 0.32 / 0.32 |
| b in η | 1.0 / 0.911 | 27 / 27 | 1.0 / 1.0 |
| b overlap (full pipeline) | Jaccard=1.0; upstream 8.2%‡ | 27 |
| min_events | 5 / 6 / 8 | 27 / 27 / 27 | 1.0 |

†Baseline: Δt = 2 yr, GK, b = 1.0, mean GC > 1500 km (`results/series_stability_venn.json`). ‡**8.2%** = 165/2017 GK mainshocks whose **`identify_clusters()` cluster label** changes when b goes from 1.0 to 0.911 (full re-run GK → `identify_clusters()` → `global_series()`; `run_sensitivity_b0911_full.py` → `sensitivity_b0911_full_pipeline.json`).

The row **b overlap (full pipeline)** reports a full pipeline re-run at b = 1.0 vs b = 0.911. **Jaccard = 1.0** means identical **series event sets** across the 27 detections — `global_series()` does not use b in η. **8.2%** upstream is the fraction of GK mainshocks whose **η-cluster label** changes at the `identify_clusters()` step; this is a different level from downstream series membership, so equal N = 27 and Jaccard = 1.0 do **not** prove unchanged upstream structure.

**Stability interpretation.** N = 27 is **stable** across declustering and b at Δt = 2 yr (4/12 parameter configs yield N = 27). **Window width** dominates N_series (53 at 1 yr, 11 at 5 yr). The liberal detector sweeps nearly all GK mainshocks into at least one candidate window at short Δt; at Δt = 2 yr the count collapses to 27 — a **detector-artifact** stability, not proof of a physically invariant “core 27.”

Sources: `sensitivity_eta_windows_gc.json`, `sensitivity_declustering.json`, `sensitivity_b0911_full_pipeline.json`, `series_stability_venn.json`.

---

## 5. Discussion

Under the **temporal-only** ETAS null implemented, detector output is **consistent with catalog-calibrated expectations** — both in-sample and on the 2001–2026 hold-out (§4.1). This bounds **temporal** excess in sliding-window candidates; it does **not** test long-range spatial linkage (Ogata, 1998 spatial kernel — future work).

The permutation test addresses a **different** null (independent event times) and is expected to reject under aftershock clustering; it is **not** evidence for teleseismic chains. Prior global rate studies (Michael, 2011; Shearer & Stark, 2012) found no anomalous M≥7 clustering; our η-detector + ETAS framework is complementary but similarly does not establish physically linked global series.

**N = 27 “super-stability”** across declustering and b at fixed Δt = 2 yr reflects **liberal detector gates** (mean GC > 1500 km sweeps most global M≥6.5 windows) rather than a robust physical invariant. Window width is the dominant sensitivity axis. We do **not** claim to have disproved global series as a phenomenon — only what these tests can establish.

**Limitations.** In-sample calibration–detector coupling; GK/ETAS model mismatch; mean GC gate weaker than all-pairs requirement; 142-window search without FDR on the 27 modern count; Bird/WLS/pre-1900 diagnostics in `paper/supplementary.md` §S1–S3.

---

## 6. Conclusions

We present a reproducible global M≥6.5 pipeline combining Baiesi–Paczuski η detection with catalog-calibrated temporal ETAS validation under explicit falsification framing. Primary inference is limited to **temporal** clustering in detector windows on the modern catalog; spatial linkage remains an open question.

The implemented tests do **not** support a discovery claim for physically validated multi-regional global series. The contribution is methodological transparency and honest null-result bounds — not confirmation or definitive rejection of long-range teleseismic coupling.

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
