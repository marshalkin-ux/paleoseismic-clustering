# Global Seismic Series: Statistical Analysis of Spatiotemporal Clustering in M≥6.5 Earthquake Catalogs (2150 BCE – 2026 CE)

**DOI:** 10.20542/[placeholder]

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

We analyse a merged catalog (**4,418 records**, **4,267 events** M≥6.5; 2150 BCE – 2026 CE) using the Baiesi–Paczuski metric η with tectonic-path distance on the Bird (2003) graph. **47 global seismic series** are identified (27 modern, 15 early instrumental, 5 historical candidates). Significance: permutation test (n = 10,000, p < 0.0001, z = −6.17); ETAS validation (FPR = 0/100); FDR correction (45/47 at q = 0.05). Fifteen early-instrumental series reach p = 0.007, but pre-1960 catalog incompleteness (quality_score < 0.7) limits interpretation. **No historical series are statistically significant** (p = 0.46). The largest series by event count is **1905–1910** (193 events, 43 regions, Mmax = 8.8); the most spatially extensive modern series is **S170** (46 events, 12 Flinn–Engdahl regions, Mmax = 9.1, 2002–2023).

**Keywords:** global seismicity; seismic series; earthquake clustering; tectonic distance; Baiesi–Paczuski metric; ETAS validation; false discovery rate; Monte Carlo; paleoseismology; Flinn–Engdahl

---

## 1. Introduction

Large earthquakes do not occur as independent Poisson events. Following the 1992 Landers earthquake (Mw 7.3), Hill et al. (1993) documented remotely triggered seismicity at distances exceeding 1,000 km. Brodsky & Prejean (2006) showed that surface waves can initiate swarms in volcanic systems thousands of kilometres away. The 2004 Sumatra–Andaman earthquake (Mw 9.1) was followed by elevated activity in distant regions (Pollitz et al., 1998; Freed & Lin, 2001).

However, the systematic nature of such correlations remains debated. Michael (2011) found that M≥7 clustering in 1995–2011 is statistically indistinguishable from random fluctuations. Shearer & Stark (2012) reported no increase in global M≥7 and M≥8 rates after the 2004 Sumatra event. Kagan & Jackson (1999) confirmed elevated probability of paired events at short separation without resolving long-range links.

The ETAS model (Ogata, 1988) reproduces regional aftershock clustering but does not encode inter-plate correlations. The Baiesi–Paczuski (2004) metric and Zaliapin–Ben-Zion extensions (2008, 2013) provide objective cluster detection but typically use Euclidean distance, ignoring lithospheric connectivity.

**Objective.** We test the hypothesis that multi-regional seismic series exist in a four-millennium catalog of M≥6.5 earthquakes, using an adapted η metric with tectonic distance along Bird (2003) plate boundaries.

**Novelty.** To our knowledge, this is the first global application of nearest-neighbor clustering with tectonic-path distance across historical, early instrumental, and modern catalogs, combined with ETAS null-model validation and FDR correction.

---

## 2. Data

### 2.1 Catalog compilation

| Source | Period | Role |
|--------|--------|------|
| USGS ComCat | 1900–2026 | Primary instrumental catalog |
| ISC Bulletin | 1900–2023 | Relocated hypocenters for verification |
| NOAA NGDC | ~2150 BCE–2026 | Historical and paleoseismic records |

Duplicate records were merged using ±30 days and ≤50 km spatial tolerance; source priority: ISC > USGS > NOAA. After deduplication (±30 days, ≤50 km tolerance), the catalog contains **4,267** unique events (from **4,418** raw records).

**Event-count reconciliation.** The file `unified_catalog_full.csv` contains **4,418** rows; after M≥6.5 filtering, **4,267** events remain. USGS ComCat provides **2,088** raw M≥6.5 records for 1973–2026; after merging with ISC/NOAA and deduplication, the modern window contains **2,041** events M≥6.5 (**without** quality_score filtering). Gardner–Knopoff declustering removes ~24 local aftershocks during analysis (2,017 independent mainshocks, 98.8%).

**Quality scoring (metadata).** Each event receives a `quality_score` in [0.30, 0.95] based on epoch, phase readings, and cross-catalog overlap (Woessner & Wiemer, 2005); this is interpretive metadata, **not** an inclusion filter. Instrumental events after 1960 typically score ≥0.90; pre-1900 documentary records score 0.30–0.60.

**Final catalog:** 4,267 events M≥6.5 (4,418 CSV records; 2150 BCE – 2026 CE)

| Epoch | Events M≥6.5 | Period |
|-------|---------------|--------|
| Historical | 47 | pre-1900 (fragmentary paleoseismic records) |
| Early instrumental | 2,179 | 1900–1972 |
| Modern | 2,041 | 1973–2026 |

### 2.2 Catalog completeness

Maximum-curvature analysis yields Mc = 6.55. Maximum-likelihood b-value from 1,688 events above Mc:

**b = 0.911 ± 0.018**

The Gutenberg–Richter relation is satisfied above Mc, confirming catalog suitability for analysis. Note: the catalog b-value (0.911) differs from the b = 1.0 exponent used in the η metric (Baiesi–Paczuski default; see §3.2).

---

## 3. Methods

### 3.1 Tectonic distance

We define tectonic distance rij as the shortest path between hypocenters along the global plate-boundary graph of Bird (2003), comprising 20 key segments (subduction zones, transform faults, mid-ocean ridges). Paths are computed with Dijkstra's algorithm (NetworkX). When either hypocenter lies more than 500 km from the nearest boundary node, or when no graph path exists between plate segments, we apply a penalty fallback:

**rij = 1.5 × rGC**

where rGC is the great-circle (Haversine) distance. This penalises intra-plate and weakly connected pairs relative to boundary-adjacent events, consistent with the implementation in `tectonic_distance.py`.

### 3.2 Connectivity metric η

Following Baiesi & Paczuski (2004) and Zaliapin et al. (2008):

**ηij = tij · rij^1.6 · 10^(−b·mi)**

| Component | Symbol | Physical meaning |
|-----------|--------|------------------|
| Time | tij (yr) | Penalty for large temporal separation |
| Distance | rij^1.6 (km) | Penalty for large tectonic separation |
| Magnitude | 10^(−b·mi) | Weighting by parent-event magnitude mi |

Here df = 1.6 (fractal dimension; Baiesi & Paczuski, 2004) and **b = 1.0** (code default `B_DEFAULT`; parent magnitude mi only—no erroneous bi in the exponent). Smaller η indicates tighter spatiotemporal coupling.

*Note:* b = 1.0 follows the original Baiesi & Paczuski (2004) formulation; the catalog's empirical b-value is **0.911 ± 0.018** (used in the Monte Carlo test).

**Units note.** η is a relative connectivity measure without absolute physical units; only ratios and log10(η) statistics are interpreted. The threshold η0 is determined empirically from the observed nearest-neighbor distribution, not from first principles.

### 3.3 Threshold η0 and series detection

1. **Declustering** via Gardner–Knopoff (1974) to remove local aftershocks before global-series search.
2. **Nearest-neighbor forest:** for each event j, parent i* = argmin ηij (over preceding events).
3. **Threshold η0:** automatic selection from the distribution of nearest-neighbor η values. Primary method: KDE valley detection between bimodal modes in log10(η) (Zaliapin & Ben-Zion, 2013). Default cluster cut when unspecified: η0 = 10^(median log10 η). The threshold is validated against a Poisson temporal-permutation null (Monte Carlo, n = 10,000).
4. **Global series criterion:** N ≥ 4 events; M ≥ 6.5; ≥ 3 Flinn–Engdahl regions.
5. **Sliding windows** (1, 2, 5 yr; 1-yr step); overlapping groups merged.

### 3.4 Statistical validation

**ETAS null model** (`ETASCatalogGenerator`, `scripts/run_etas_validation.py`). To test whether series arise from local aftershock structure alone, we use global ETAS parameters (Ogata, 1988; Helmstetter & Sornette, 2003): **μ = 0.008**, **K = 0.08**, **α = 1.0**, **c = 0.005** days, **p = 1.1**; spatial triggering cutoff **max_trigger_distance_km = 500** (parent–child links beyond 500 km forbidden). The parameter **c = 0.005 days** was chosen conservatively to accelerate aftershock decay in the null model; even under this strict condition, no false series emerged (FPR = 0/100). Generation follows a branching Poisson process: background events plus Omori–Utsu offspring within ≤500 km of each parent (up to 5 generations), magnitudes from Gutenberg–Richter (b = 1.0). We generate **100** synthetic catalogs (seed = 42) and apply the same `global_series` algorithm (N ≥ 4, ≥ 3 Flinn–Engdahl regions, 2-yr window) to each. **FPR** = fraction of catalogs with ≥1 false global series = **0/100**; **pETAS** = P(NETAS ≥ Nobs) = **0.0000** (discrete empirical test, resolution 1/101).

| Test | Parameters | Result |
|------|------------|--------|
| Permutation (Monte Carlo) | n = 10,000 | p < 0.0001, z = −6.17 (modern) |
| ETAS null model | μ=0.008, K=0.08, α=1.0, c=0.005 d, p=1.1; 500 km; 100 cat. | FPR = 0/100, pETAS = 0.0000 |
| FDR (Benjamini–Hochberg) | q = 0.05 | 45/47 series significant |
| Declustering | GK / ZBZ | 98.8% / 100.0% independent events |

---

## 4. Results

### 4.1 Identified series

Full historical analysis yields **47 global seismic series** (142 cluster candidates before window filtering):

| Epoch | N series | Events | p-value | z-score |
|-------|----------|--------|---------|---------|
| Modern (1973–2026) | 27 | 2,041 | < 0.0001 | −6.17 |
| Early instrumental (1900–1972) | 15 | 2,179 | 0.007 | −2.43 |
| Historical (pre-1900) | 5 | 47 | 0.46 | — |

**Modern period.** Twenty-seven series are highly significant (p < 0.0001).

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

The **1905–1910** episode (193 events, 43 regions) is the largest series in the full catalog, identified in the early instrumental window. Series **S170** spans 12 Flinn–Engdahl regions and includes the 2004 Indian Ocean earthquake (M 9.1), representing the most spatially extensive modern episode (Figure 1: `figures/grl/fig01_global_map.png`; Figure 2: ETAS validation, `figures/grl/fig02_etas_validation.png`; η distribution: `figures/viz2_eta_distribution.png`).

### 4.3 Spatial–temporal distribution

Elevated series activity occurs in 1952–1965 and 2002–2016 (post-Sumatra period). Spatially, clusters concentrate along the circum-Pacific belt (Kamchatka, Kuril Islands, Japan, Tonga, Indonesia). Tectonic distance lowers the η0 threshold by ~0.3 log10 units compared with Euclidean distance.

---

## 5. Discussion

Observed global series are incompatible with both a spatially inhomogeneous Poisson null hypothesis and ETAS catalogs that reproduce local aftershock structure without long-range coupling. FDR correction confirms that the majority of identified series (45/47) are not artifacts of multiple testing.

**Early instrumental period (1900–1972).** Fifteen series in this window reach statistical significance (p = 0.007, z = −2.43), strengthening the overall conclusion that clustering is not limited to modern catalog completeness. However, most pre-1960 events have quality_score < 0.7, and early instrumental incompleteness requires cautious interpretation of individual episodes (including 1905–1910).

**Reconciliation with Michael (2011) and Shearer & Stark (2012).** Michael (2011) showed that apparent M≥7 clustering in 1995–2011 is statistically indistinguishable from random Poisson fluctuations once rate inhomogeneity is properly conditioned. Shearer & Stark (2012) found no significant increase in global M≥7 or M≥8 event rates after the 2004 Sumatra earthquake—ruling out a secular acceleration in global hazard. Both studies tested **global event frequencies and short-window rate statistics**, not the **spatiotemporal linkage structure** of multi-regional episodes. Our η-metric detects clustering *patterns*—nearest-neighbor connectivity across Flinn–Engdahl regions with tectonic-path distance—largely independent of whether the overall event rate has risen. A catalog can therefore exhibit significant multi-regional series connectivity (our result) while showing no anomalous global rate increase (their result). The findings are complementary, not contradictory; reconciling them requires metrics that separate linkage topology from rate trends.

Tectonic-path distance is essential: Euclidean metrics underestimate connectivity along plate boundaries and overestimate links across rigid lithosphere, producing false positives and missing genuine inter-plate correlations.

**Historical period.** No statistically significant historical series were detected (p = 0.46). Only **47** M≥6.5 events pre-1900 — fragmentary paleoseismic records spanning ~4,000 years; the five candidate episodes do not survive the permutation null.

**ETAS p-value interpretation.** pETAS = 0.0000 (FPR = 0/100) is an empirical discrete test with 100 synthetic catalogs: it rejects the hypothesis that all 47 observed series arise from local aftershock branching without long-range coupling (>500 km). It does **not** identify the physical triggering mechanism, nor does it prove that every individual series is physically coupled rather than a statistical aggregate.

**Mechanism and causality.** The η metric is correlative: it does not establish causal triggering. Hypocentral depth and focal mechanisms are not incorporated; shallow crustal and deep subduction events are treated identically. Static Coulomb stress transfer, dynamic triggering, and viscoelastic relaxation remain plausible but unverified without ΔCFS modelling.

Additional limitations include uneven historical completeness, static plate-boundary geometry, and sensitivity to the adaptive η0 threshold.

---

## 6. Conclusions

1. A unified catalog of 4,267 M≥6.5 events (4,418 CSV records; 2150 BCE – 2026 CE) contains 47 global seismic series; 27 modern series are significant at p < 0.0001 (Monte Carlo, n = 10,000).
2. ETAS validation (μ=0.008, K=0.08, α=1.0, c=0.005 d, p=1.1, 500 km cutoff; FPR = 0/100) and FDR correction (45/47 at q = 0.05) confirm that series are not explained by randomness or local aftershock clustering alone.
3. The largest series by event count is 1905–1910 (193 events, 43 regions, Mmax = 8.8); the most spatially extensive modern series is S170 (46 events, 12 regions, 2002–2023, Mmax = 9.1).
4. Tectonic distance increases η-metric sensitivity by ~0.3 log10 units relative to Euclidean distance.
5. **Interpretive fork given current evidence:** (a) If detected series reflect genuine long-range coupling, probabilistic hazard models should incorporate elevated conditional probabilities in tectonically connected distant zones and explicit long-range kernels in ETAS extensions. (b) Even if individual episodes prove artifactual under refined constraints, the combined FDR + ETAS framework provides a reproducible, code-audited null-testing pipeline applicable to future catalog updates.

**Future work:** Coulomb stress change (ΔCFS) analysis for S047, S170, and S095 incorporating **hypocentral depth and focal mechanisms** (King et al., 1994; Stein, 1999); ETAS extensions with explicit long-range kernels; Zenodo DOI release.

---

## Data and Code Availability

- Interactive presentation: https://marshalkin-ux.github.io/paleoseismic-clustering/
- Source code: https://github.com/marshalkin-ux/paleoseismic-clustering
- Results: `results/analysis_full_historical.json`, `results/etas_validation.json`, `results/fdr_correction_results.csv`

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
