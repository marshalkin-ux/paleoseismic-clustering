# Global Seismic Series: Statistical Analysis of Spatiotemporal Clustering in M≥6.5 Earthquake Catalogs (2150 BCE – 2026 CE)

**DOI:** 10.20542/[placeholder]

© 2026 **Yaroslav Marshalkin**

---

## Metadata

**Author:** Yaroslav Marshalkin  
**Email:** marshalkin@gmail.com · **Telegram:** [@MRSHLKN](https://t.me/MRSHLKN)  
**Repository:** [github.com/marshalkin-ux/paleoseismic-clustering](https://github.com/marshalkin-ux/paleoseismic-clustering)  
**Interactive demo:** [marshalkin-ux.github.io/paleoseismic-clustering](https://marshalkin-ux.github.io/paleoseismic-clustering/)

---

## Abstract

Whether large earthquakes cluster in space and time beyond chance is a foundational question in probabilistic seismic hazard assessment. We analyse a merged catalog of **4,418 earthquakes** with M≥6.5 spanning 2150 BCE to 2026 CE, compiled from USGS ComCat, the ISC Bulletin, and NOAA NGDC (catalog completeness Mc = 6.55; Gutenberg–Richter b = 0.911 ± 0.018). Using the Baiesi–Paczuski nearest-neighbor metric η with **tectonic-path distance** on the Bird (2003) plate-boundary graph, we identify **47 global seismic series** across three temporal windows: 27 in the modern period (1973–2026), 15 in the early instrumental period (1900–1972), and 5 historical episodes (pre-1900). Significance is established through a three-level framework: (i) a permutation test (n = 10,000, p < 0.0001, z = −6.17); (ii) ETAS null-model validation (100 synthetic catalogs without long-range coupling, pETAS = 0.0000, false-positive rate 0/100); and (iii) Benjamini–Hochberg false discovery rate correction at q = 0.05 (**45/47** series remain significant). The largest modern series, S170, comprises 46 events across 12 Flinn–Engdahl regions (2002–2023, Mmax = 9.1), including the 2004 Sumatra–Andaman earthquake. Tectonic distance improves clustering sensitivity by ~0.3 log10 η units relative to Euclidean distance.

**Keywords:** global seismicity; seismic series; earthquake clustering; tectonic distance; Baiesi–Paczuski metric; ETAS validation; false discovery rate; Monte Carlo; paleoseismology; remote triggering

---

## 1. Introduction

Large earthquakes do not occur as independent Poisson events. Following the 1992 Landers earthquake (Mw 7.3), Hill et al. (1993) documented remotely triggered seismicity at distances exceeding 1,000 km. Brodsky & Prejean (2006) showed that surface waves can initiate swarms in volcanic systems thousands of kilometres away. The 2004 Sumatra–Andaman earthquake (Mw 9.1) was followed by elevated activity in distant regions, interpreted by some authors as long-term global stress perturbation (Pollitz et al., 1998; Freed & Lin, 2001).

However, the systematic nature of such correlations remains debated. Michael (2011) found that M≥7 clustering in 1995–2011 is statistically indistinguishable from random fluctuations. Shearer & Stark (2012) reported no increase in global M≥7 and M≥8 rates after the 2004 Sumatra event. Kagan & Jackson (1999) demonstrated elevated probability of paired events at short separation, confirming local correlations without resolving long-range links.

The ETAS model (Ogata, 1988) reproduces regional aftershock clustering but does not encode inter-plate correlations. The Baiesi–Paczuski (2004) metric and its Zaliapin–Ben-Zion extensions (2008, 2013) provide objective cluster detection but typically use Euclidean distance, ignoring lithospheric connectivity.

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

Duplicate records were merged using ±30 days and ≤50 km spatial tolerance; source priority: ISC > USGS > NOAA. Only events with quality_score > 0.5 were retained.

**Final catalog:** 4,418 events M≥6.5 (2150 BCE – 2026 CE)

| Epoch | Events | Period |
|-------|--------|--------|
| Historical | 67 | pre-1900 |
| Early instrumental | 2,179 | 1900–1972 |
| Modern | 2,041 | 1973–2026 |

### 2.2 Catalog completeness

Maximum-curvature analysis yields Mc = 6.55. Maximum-likelihood b-value from 1,688 events above Mc:

**b = 0.911 ± 0.018**

The Gutenberg–Richter relation is satisfied above Mc, confirming catalog suitability for analysis.

---

## 3. Methods

### 3.1 Tectonic distance

We define tectonic distance rij as the shortest path between hypocenters along the global plate-boundary graph of Bird (2003), comprising 20 key segments (subduction zones, transform faults, mid-ocean ridges). Paths are computed with Dijkstra's algorithm (NetworkX). For weakly connected plate pairs (rtect > 1.5 × reucl), a penalty factor rij = 1.5 × reucl is applied.

### 3.2 Connectivity metric η

Following Baiesi & Paczuski (2004) and Zaliapin et al. (2008):

**ηij = tij · rij^1.6 · 10^(−b·mi)**

| Component | Symbol | Physical meaning |
|-----------|--------|------------------|
| Time | tij (yr) | Penalty for large temporal separation |
| Distance | rij^1.6 (km) | Penalty for large tectonic separation |
| Magnitude | 10^(−b·mi) | Weighting by parent-event magnitude |

Here df = 1.6 (fractal dimension; Baiesi & Paczuski, 2004).

### 3.3 Series detection algorithm

1. Declustering via Gardner–Knopoff (1974) to remove local aftershocks.
2. Nearest-neighbor forest: for each event j, parent i* = argmin ηij subject to ηij < η0.
3. Global series criterion: N ≥ 4 events; M ≥ 6.5; ≥ 3 Flinn–Engdahl regions.
4. Sliding windows (1, 2, 5 yr; 1-yr step); overlapping groups merged.

### 3.4 Statistical validation

| Test | Parameters | Result |
|------|------------|--------|
| Permutation (Monte Carlo) | n = 10,000 | p < 0.0001, z = −6.17 (modern) |
| ETAS null model | 100 synthetic catalogs | 0 false series, pETAS = 0.0000 |
| FDR (Benjamini–Hochberg) | q = 0.05 | 45/47 series significant |
| Declustering | GK / ZBZ | 98.8% / 100.0% independent events |

---

## 4. Results

### 4.1 Identified series

Full historical analysis yields **47 global seismic series**:

| Epoch | N series | p-value | z-score |
|-------|----------|---------|---------|
| Modern (1973–2026) | 27 | < 0.0001 | −6.17 |
| Early instrumental (1900–1972) | 15 | 0.007 | −2.43 |
| Historical (pre-1900) | 5 | 0.46 | — |

The algorithm identifies 142 cluster candidates before window filtering and FDR correction.

### 4.2 Top five multi-regional series

| Series | N | Regions | Mmax | Period | qBH |
|--------|---|---------|------|--------|-----|
| S047 | 53 | 5 | 8.0 | 1982–2024 | 9.7×10⁻⁵ |
| S170 | 46 | 12 | 9.1 | 2002–2023 | 1.2×10⁻⁴ |
| S095 | 25 | 4 | 7.9 | 1989–2017 | 3.4×10⁻³ |
| S116 | 22 | 5 | 8.2 | 1993–2021 | 4.1×10⁻³ |
| S191 | 15 | 4 | 8.4 | 2007–2022 | 7.3×10⁻³ |

Series S170 spans 12 Flinn–Engdahl regions and includes the 2004 Indian Ocean earthquake (M 9.1), representing the most spatially extensive modern episode.

### 4.3 Spatial–temporal distribution

Elevated series activity occurs in 1952–1965 and 2002–2016 (post-Sumatra period). Spatially, clusters concentrate along the circum-Pacific belt (Kamchatka, Kuril Islands, Japan, Tonga, Indonesia). Tectonic distance lowers the η0 threshold by ~0.3 log10 units compared with Euclidean distance.

---

## 5. Discussion

Observed global series are incompatible with both a spatially inhomogeneous Poisson null hypothesis and ETAS catalogs that reproduce local aftershock structure without long-range coupling. FDR correction confirms that the majority of identified series (45/47) are not artifacts of multiple testing.

Tectonic-path distance is essential: Euclidean metrics underestimate connectivity along plate boundaries and overestimate links across rigid lithosphere, producing false positives and missing genuine inter-plate correlations.

Historical episodes (e.g., 856–887 CE: six M≥7.5 events across Iran, Japan, Spain, and Greece within 30 years) exceed typical dynamic-triggering timescales and warrant further investigation with expanded paleoseismic constraints.

Limitations include uneven historical completeness, static plate-boundary geometry, and the correlative (non-causal) nature of the η metric.

---

## 6. Conclusions

1. A unified catalog of 4,418 M≥6.5 events (2150 BCE – 2026 CE) contains 47 global seismic series; 27 modern series are significant at p < 0.0001 (Monte Carlo, n = 10,000).
2. ETAS validation (0/100 false positives) and FDR correction (45/47 at q = 0.05) confirm that series are not explained by randomness or local aftershock clustering alone.
3. Series S170 (46 events, 12 regions, 2002–2023, Mmax = 9.1) demonstrates long-term global activation along the Pacific Ring of Fire.
4. Tectonic distance increases η-metric sensitivity by ~0.3 log10 units relative to Euclidean distance.

**Future work:** Coulomb stress change (ΔCFS) analysis for S047, S170, and S095; focal mechanism constraints; ETAS extensions with explicit long-range kernels; Zenodo DOI release.

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
8. Michael A.J. (2011). Random variability explains apparent global clustering of large earthquakes. *Geophys. Res. Lett.*, 38, L21301.
9. Shearer P.M., Stark P.B. (2012). Global risk of big earthquakes has not recently increased. *PNAS*, 109(3), 717–721.
10. Ogata Y. (1988). Statistical models for earthquake occurrences and residual analysis. *J. Amer. Stat. Assoc.*, 83, 9–27.
11. Benjamini Y., Hochberg Y. (1995). Controlling the false discovery rate. *J. Roy. Stat. Soc. B*, 57(1), 289–300.
12. Gardner J.K., Knopoff L. (1974). Is the sequence of earthquakes in Southern California Poissonian? *BSSA*, 64, 1363–1367.
13. Young J.B. et al. (1996). The Flinn–Engdahl regionalization scheme: the 1995 revision. *Phys. Earth Planet. Int.*, 96, 223–297.

---

## Acknowledgments

The author acknowledges USGS, NOAA NGDC, and the ISC for maintaining open seismic catalogs. This work received no targeted funding.

**Corresponding author:** Yaroslav Marshalkin, marshalkin@gmail.com
