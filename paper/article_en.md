# Global Seismic Series: Statistical Analysis of Spatiotemporal Clustering in M≥6.5 Earthquake Catalogs (1973–2026 CE)

*Four-millennium catalog (2150 BCE–2026; 4,267 M≥6.5 events); robust significance analysis on 2,041 modern + 2,179 early instrumental events; 47 pre-1900 records not used for significance claims.*

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

We analyse a merged catalog of **4,267 unique M≥6.5 events** (from 4,418 saved CSV rows; ~151 NOAA records with M<6.5 from an M≥6.0 fetch **retained in CSV for provenance but excluded from all clustering analyses**) using the Baiesi–Paczuski metric η with tectonic-path distance on the Bird (2003) graph. **Significance claims focus on the modern instrumental window (1973–2026, 2,041 events) and early instrumental period (1900–1972, 2,179 events);** 47 pre-1900 records are retained for context but not used for epoch-level significance. **47 global seismic series** are identified (27 modern, 15 early instrumental, 5 historical candidates). Significance: permutation test (n = 10,000, **p ≤ 0.0001**[^mc-p], z = −6.17); ETAS validation on modern window (**n = 1000** synthetic catalogs, **FPR = 1000/1000** catalogs with ≥1 spurious series, mean **15.4 ± 1.7**; max **24**; **pETAS = 0/1000** for N_obs = 27); FDR correction (45/47 at q = 0.05, **N = 47** hypotheses). Fifteen early-instrumental series reach p = 0.007, but pre-1960 catalog incompleteness (quality_score < 0.7) limits interpretation. **No historical series are statistically significant** (p = 0.46). The largest series by event count is **1905–1910** (193 events, 43 regions, Mmax = 8.8); the most spatially extensive modern series is **S170** (46 events, 12 Flinn–Engdahl regions, Mmax = 9.1, 2002–2023). Tectonic-path distance applies a real Dijkstra path for **~2%** of audited pairs (98% GC fallback). Series detection is a **statistical anomaly** (η links, p-values); causal mechanism is not established.

[^mc-p]: Discrete permutation test with n = 10,000 yields minimum achievable p = 1/(n+1) = 0.0001; we report p ≤ 0.0001 rather than p < 0.0001.

**Keywords:** global seismicity; seismic series; earthquake clustering; tectonic distance; Baiesi–Paczuski metric; ETAS validation; false discovery rate; Monte Carlo; paleoseismology; Flinn–Engdahl

---

## 1. Introduction

Large earthquakes do not occur as independent Poisson events. Following the 1992 Landers earthquake (Mw 7.3), Hill et al. (1993) documented remotely triggered seismicity at distances exceeding 1,000 km. Brodsky & Prejean (2006) showed that surface waves can initiate swarms in volcanic systems thousands of kilometres away. The 2004 Sumatra–Andaman earthquake (Mw 9.1) was followed by elevated activity in distant regions (Pollitz et al., 1998; Freed & Lin, 2001).

However, the systematic nature of such correlations remains debated. Michael (2011) tested whether global M≥7 clustering in 1995–2011 exceeds Poisson rate fluctuations. Shearer & Stark (2012) tested whether global M≥7 and M≥8 rates increased after the 2004 Sumatra event. Kagan & Jackson (1999) confirmed elevated probability of paired events at short separation without resolving long-range links.

The ETAS model (Ogata, 1988) reproduces regional aftershock clustering but does not encode inter-plate correlations. The Baiesi–Paczuski (2004) metric and Zaliapin–Ben-Zion extensions (2008, 2013) provide objective cluster detection but typically use Euclidean distance, ignoring lithospheric connectivity.

**Objective.** We test the hypothesis that multi-regional seismic series exist in a four-millennium M≥6.5 catalog, with **primary significance claims on the modern instrumental window (1973–2026)**, using an adapted η metric with tectonic distance along Bird (2003) plate boundaries.

**Scope.** We combine nearest-neighbor clustering with tectonic-path distance, ETAS null-model validation, and FDR correction across historical, early instrumental, and modern epochs; this extends prior global rate tests (Michael 2011; Shearer & Stark 2012) with a complementary η-linkage statistic but does not supersede their conclusions.

---

## 2. Data

### 2.1 Catalog compilation

| Source | Period | Role |
|--------|--------|------|
| USGS ComCat | 1900–2026 | Primary instrumental catalog |
| ISC Bulletin | 1900–2023 | Relocated hypocenters for verification |
| NOAA NGDC | ~2150 BCE–2026 | Historical and paleoseismic records |

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

**Final catalog:** 4,267 events M≥6.5 (4,418 CSV records; 2150 BCE – 2026 CE)

| Epoch | Events M≥6.5 | Period |
|-------|---------------|--------|
| Historical | 47 | pre-1900 (fragmentary paleoseismic records) |
| Early instrumental | 2,179 | 1900–1972 |
| Modern | 2,041 | 1973–2026 |

### 2.2 Catalog completeness

Maximum-curvature analysis yields Mc = 6.55. Maximum-likelihood b-value from 1,688 events above Mc:

**b = 0.911 ± 0.018**

The Gutenberg–Richter relation is satisfied above Mc. **b-value consistency:** clustering η uses **b = 1.0** per the Baiesi & Paczuski (2004) convention for cross-catalog comparability; the Monte Carlo null and completeness analysis use the fitted **b = 0.911 ± 0.018**. This difference is intentional: η is a relative connectivity measure, not a rate forecast.

---

## 3. Methods

### 3.1 Tectonic distance

We define tectonic distance rij as the shortest path between hypocenters along the global plate-boundary graph of Bird (2003), comprising 20 key segments (subduction zones, transform faults, mid-ocean ridges). Paths are computed with Dijkstra's algorithm (NetworkX). When either hypocenter lies more than 500 km from the nearest boundary node, or when no graph path exists between plate segments, we apply a penalty fallback:

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
| Distance | rij^1.6 (km) | Penalty for large tectonic separation |
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
 η NN forest (Bird 2003 tectonic distance)
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

**ZBZ — supplement/sensitivity only.** Zaliapin–Ben-Zion (2040/2,041 independent) is reported **only as a sensitivity check** in supplementary comparison (`run_declustering_comparison.py`), not as a co-primary or sequential filter. GK and ZBZ answer different questions and are not combined in the main pipeline.

### 3.4 Threshold η0, series detection, and ETAS parameters

1. **Declustering** via Gardner–Knopoff (1974) — mainshocks for NN search.
2. **Nearest-neighbor forest:** for each event j, parent i* = argmin ηij.
3. **Threshold η0:** automatic selection from the distribution of nearest-neighbor η values. Primary method: KDE valley detection between bimodal modes in log10(η) (Zaliapin & Ben-Zion, 2013). Default cluster cut when unspecified: η0 = 10^(median log10 η). The threshold is validated against a Poisson temporal-permutation null (Monte Carlo, n = 10,000).
4. **Global series criterion:** N ≥ 4 events; M ≥ 6.5; ≥ 3 Flinn–Engdahl regions.
5. **Sliding windows** (1, 2, 5 yr; 1-yr step); overlapping groups merged.

**ETAS null-model parameters (not catalog-calibrated).** ETAS validation uses **default global parameters** (μ = 0.008, K = 0.08, α = 1.0, c = 0.005 d, p = 1.1; Helmstetter & Sornette, 2003), **not** values re-calibrated on the 2,041-event modern catalog (`results/etas_calibration_note.md`, `scripts/calibrate_etas.py`). Rejecting the ETAS null therefore tests whether our series exceed a **literature-standard** local-aftershock model, not a catalog-specific fit. Optional homogeneous Poisson MLE on catalog event times yields **μ ≈ 0.105 events/day** vs the default 0.008 — full spatial ETAS MLE and multi-seed robustness (`scripts/run_etas_multiseed.py`) are future work.

### 3.5 Statistical validation

**FDR procedure.** Sliding windows (1, 2, and 5 yr; 1-yr step) over the η NN forest yield **142 cluster candidates** before merging overlapping groups. After merge and series criteria (N ≥ 4, M ≥ 6.5, ≥ 3 Flinn–Engdahl regions), **47 global series** remain. Benjamini–Hochberg FDR (q = 0.05) is applied to **N = 47** series-level p-values (one hypothesis per merged series), not to individual window tests or NN pairs. Result: **45/47** significant. See `results/fdr_correction_results.csv`.

**ETAS null model.** We generate **1000** synthetic catalogs (**seed = 42**; Flinn–Engdahl regions via KD-tree lookup). The same series-detection algorithm (N ≥ 4, ≥ 3 Flinn–Engdahl regions, 2-yr window) is applied to each catalog. On the real modern catalog the algorithm finds **N_obs = 27** series. On ETAS nulls: **1000/1000** catalogs contain ≥1 spurious series (**FPR = 1.0**); mean spurious count **15.4 ± 1.7** (max **24**). **pETAS = P(N_ETAS ≥ 27) = 0/1000** (report as **≤ 0.001**). Note: previously reported FPR = 0/100 arose from an API bug (`min_regions` kwarg caused TypeError → returned 0); corrected in this revision.

| Test | Parameters | Result |
|------|------------|--------|
| Permutation (Monte Carlo) | n = 10,000 | p ≤ 0.0001[^mc-p], z = −6.17 (modern) |
| ETAS null model | μ=0.008, K=0.08; 500 km; 1000 cat.; N_obs=27 | FPR = 1000/1000; mean 15.6 series; pETAS ≤ 0.001 |
| FDR (Benjamini–Hochberg) | q = 0.05; N = 47 series | 45/47 significant |
| Declustering (primary) | GK | 2,017/2,041 (24 aftersh.) |

**Verified from code.** Series counts and epoch p-values: `results/analysis_full_historical.json`. Monte Carlo (p, z): `results/montecarlo_full.json`. ETAS (FPR, p_ETAS): `results/etas_validation.json`. FDR (45/47): `results/fdr_correction_results.csv`. GK/ZBZ counts: `scripts/run_declustering_comparison.py`. Tectonic diagnostic (median Δlog₁₀η = +0.28): `scripts/generate_grl_figures.py::fig_tectonic_vs_euclidean`.

---

## 4. Results

### 4.1 Identified series

Full historical analysis yields **47 global seismic series** (142 cluster candidates before window filtering):

| Epoch | N series | Events | p-value | z-score |
|-------|----------|--------|---------|---------|
| Modern (1973–2026) | 27 | 2,041 | ≤ 0.0001 | −6.17 |
| Early instrumental (1900–1972) | 15 | 2,179 | 0.007 | −2.43 |
| Historical (pre-1900) | 5 | 47 | 0.46 | — |

**Modern period.** Twenty-seven series are highly significant (p ≤ 0.0001).

**Early instrumental period.** Fifteen series reach p = 0.007, but this result must be interpreted cautiously: most pre-1960 events have quality_score < 0.7, and catalog incompleteness inflates inter-event intervals, reducing detection power.

**Historical period.** **No statistically significant historical series** were detected (p = 0.46). Only **47** M≥6.5 events pre-1900 — fragmentary paleoseismic records spanning ~4,000 years; the five candidate episodes do not survive the permutation null.

### 4.2 Top five multi-regional series

| Series | N | Regions | Mmax | Period | qBH |
|--------|---|---------|------|--------|-----|
| 1905–1910 | 193 | 43 | 8.8 | 1905–1910 | — |
| S047 | 53 | 5 | 8.0 | 1982–2024 | 9.7×10⁻⁵ |
| S170 | 46 | 12 | 9.1 | 2002–2023 | 1.2×10⁻⁴ |
| S095 | 25 | 4 | 7.9 | 1989–2017 | 3.4×10⁻³ |
| S116 | 22 | 5 | 8.2 | 1993–2021 | 4.1×10⁻³ |

The **1905–1910** episode (193 events, 43 regions) is the largest series in the full catalog, identified in the early instrumental window. Series **S170** spans 12 Flinn–Engdahl regions and includes the 2004 Indian Ocean earthquake (M 9.1), representing the most spatially extensive modern episode (Figures 1–2 in the repository).

### 4.3 Spatial–temporal distribution

Elevated series activity occurs in 1952–1965 and 2002–2016 (post-Sumatra period). Spatially, clusters concentrate along the circum-Pacific belt (Kamchatka, Kuril Islands, Japan, Tonga, Indonesia). The tectonic-vs-Euclidean diagnostic (§3.1) reports median Δlog₁₀η = +0.28 on random pairs; this reflects the 1.5× GC fallback for most samples, not a validated η₀ shift.

---

## 5. Discussion

### 5.1 Statistical anomaly vs physical mechanism

**Statistical anomaly (established):** Observed global series are incompatible with Poisson and local-only ETAS nulls (>500 km cutoff). FDR correction confirms 45/47 series. This is a conclusion about **η links and p-values**, not causality.

**Physical mechanism (not established):** The η metric is correlative; hypocentral depth and focal mechanisms are not incorporated. Preliminary Coulomb/dynamic stress tests for S170 did not reach triggering thresholds (see repository supplement). **Series detection does not imply direct triggering**; co-occurrence may reflect shared tectonic loading, mantle coupling, or catalog incompleteness artifacts.

**Early instrumental period (1900–1972).** Fifteen series reach p = 0.007 (z = −2.43), but quality_score < 0.7 before 1960 limits interpretation of individual episodes (including 1905–1910).

**Reconciliation with Michael (2011) and Shearer & Stark (2012).** Michael tested complementary Poisson **rate** nulls for global M≥7 clustering; Shearer & Stark tested whether post-2004 **event rates** increased. Our η-linkage test adds a **different statistic** (multi-regional nearest-neighbor structure) but **does not supersede** their conclusions about rates and short-window clustering models. The findings are complementary, not contradictory.

The tectonic diagnostic (§3.1; median Δlog₁₀η = +0.28) quantifies the GC-fallback penalty on random pairs; only **~2%** of audited boundary-proximal pairs use a real Dijkstra path (§3.1)—the metric adds limited value beyond Euclidean distance for most pairs.

### 5.2 Working hypotheses (not claims)

Correlative η links **do not prove** any single mechanism. Possible (unverified) explanations for long-range coupling include:

- **Viscoelastic mantle coupling** — stress redistribution over months to years after major ruptures (Pollitz et al., 1998).
- **Dynamic triggering by surface waves** — short-lived activation at thousands of kilometres (Hill et al., 1993; Brodsky & Prejean, 2006).
- **Shared tectonic loading / stress redistribution** — secular loading without direct triggering (Freed & Lin, 2001).

Co-occurrence within a series may reflect any of these (or other) processes, or catalog artifacts.

### 5.5 Limitations

**(1) Historical period:** p = 0.46; only 47 M≥6.5 events pre-1900 — not used for significance claims.

**(2) ETAS parameters and detector calibration.** Literature-default ETAS parameters (not catalog-calibrated). The sliding-window detector is **liberal** on ETAS nulls (FPR = 1000/1000 for ≥1 series; mean 15.4), but observed modern count (27) still exceeds the ETAS null maximum (24). Multi-seed sweeps remain future work.

**(3) Tectonic distance:** 500 km / 1.5× GC approximations; **98%** of audited pairs use GC fallback (4987 pairs, §3.1); real Dijkstra paths for **~2%** only.

**(4) Declustering asymmetry.** GK is primary in `pipeline_v2.py`; full-epoch `run_full_historical_analysis.py` does not pre-filter with GK.

**(5) FDR scope.** BH correction applies to N = 47 merged series, not 142 window candidates or individual η links.

**(6) Causality:** series ≠ direct triggering; shared loading and mantle coupling are alternative explanations.

**(7) Catalog completeness.** Pre-1960 quality_score < 0.7 limits early-instrumental interpretation; Mc = 6.55 and b-value estimates apply to the instrumental subset.

---

## 6. Conclusions

1. A unified catalog of 4,267 M≥6.5 events (4,418 CSV records; spans 2150 BCE–2026) contains 47 global seismic series; **27 modern series are significant at p ≤ 0.0001** (Monte Carlo, n = 10,000).
2. ETAS validation (1000 catalogs; FPR = 1000/1000 for ≥1 spurious series; pETAS ≤ 0.001 for N_obs = 27) and FDR (45/47, N = 47) confirm that the modern series count exceeds the ETAS null envelope.
3. The largest series by event count is 1905–1910 (193 events, 43 regions, Mmax = 8.8); the most spatially extensive modern series is S170 (46 events, 12 regions, 2002–2023, Mmax = 9.1).
4. Tectonic-path distance: **2.0%** of 4987 audited pairs use a real Dijkstra path, **98.0%** the 1.5× GC fallback; median Δlog₁₀η = +0.28 (§3.1).
5. **Interpretive fork** (statistics vs mechanism): **(a)** if η links reflect genuine spatiotemporal structure — hazard implications and long-range ETAS kernels (without claiming direct triggering); **(b)** if episodes prove artifactual — FDR + ETAS remains a reproducible null-test pipeline. **Series detection does not imply direct triggering;** co-occurrence may reflect shared tectonic loading or mantle coupling.

**Future work / supplement:** Static ΔCFS and dynamic stress for S170, S047, S095 (`results/cfs_s170_analysis.json`, `results/dynamic_stress_sumatra2004.json`); full ETAS MLE and multi-seed robustness. External DOI deposition (Zenodo) deferred — GitHub only.

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
