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

We analyse a merged catalog of **4,267 unique M≥6.5 events** (from 4,418 saved CSV rows; ~151 NOAA records with M<6.5 from an M≥6.0 fetch **retained in CSV for provenance but excluded from all clustering analyses**; 2150 BCE – 2026 CE) using the Baiesi–Paczuski metric η with tectonic-path distance on the Bird (2003) graph. **47 global seismic series** are identified (27 modern, 15 early instrumental, 5 historical candidates). Significance: permutation test (n = 10,000, p < 0.0001, z = −6.17); ETAS validation (FPR = 0/100, seed = 42); FDR correction (45/47 at q = 0.05). Fifteen early-instrumental series reach p = 0.007, but pre-1960 catalog incompleteness (quality_score < 0.7) limits interpretation. **No historical series are statistically significant** (p = 0.46). The largest series by event count is **1905–1910** (193 events, 43 regions, Mmax = 8.8); the most spatially extensive modern series is **S170** (46 events, 12 Flinn–Engdahl regions, Mmax = 9.1, 2002–2023). Series detection is a **statistical anomaly** (η links, p-values); causal mechanism is not established.

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

Duplicate records were merged using ±30 days and ≤50 km spatial tolerance; source priority: ISC > USGS > NOAA. After deduplication, the catalog contains **4,267** unique M≥6.5 events (from **4,418** saved CSV rows). **151 sub-threshold rows** (NOAA, M<6.5 from the M≥6.0 fetch) **are retained in CSV for provenance but excluded from all clustering and series-detection steps**.

**Table: Catalog merge reconciliation**

| Stage | Count | Notes |
|-------|------:|-------|
| CSV rows saved | 4,418 | Includes ~151 events M<6.5 from NOAA (M≥6.0 fetch) |
| Excluded from analysis (M<6.5) | ~151 | Provenance in CSV; not used in clustering |
| Unique M≥6.5 after dedup | 4,267 | ±30 days, ≤50 km; **analysis catalog** |
| USGS ComCat raw (1973–2026) | 2,088 | Legacy instrumental catalogue |
| Modern window after merge/ISC | 2,041 | Full merged catalog |
| GK mainshocks (modern) | 2,017 | ~24 local aftershocks removed (98.8%) |
| ZBZ independent (modern) | 2,040 | 1 dependent event (100.0%); sensitivity check |

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

**Limitations and validation.** The 500 km boundary snap and 1.5× great-circle fallback are **approximations**, not verified against independent geodetic data. Intraplate pairs rely entirely on the GC penalty. Qualitatively, tectonic-path distance vs haversine improves inter-plate η links by ~0.3 log10 η (median difference) relative to Euclidean distance (`figures/grl/fig05_tectonic_vs_euclidean.png`, §4.3); full metric validation without ground-truth data is not possible.

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

**Primary declustering.** In the canonical pipeline (`pipeline_v2.py`, `decluster_method='gardner_knopoff'`), **Gardner–Knopoff (GK) is the primary** pre-processing step: mainshocks feed the η NN forest and sliding-window series search. For the modern window (1973–2026), GK removes ~24 local aftershocks (2,017/2,041, 98.8%). The epoch script `run_full_historical_analysis.py` (47 series across epochs) applies `global_series()` to the full M≥6.5 list **without** an explicit GK pre-filter; GK/ZBZ statistics in Table §2.1 come from a separate run (`run_declustering_comparison.py`).

**ZBZ — sensitivity check only.** Zaliapin–Ben-Zion flags 1 dependent event (2,040/2,041, 100.0%) in a **separate** run, not as a sequential filter after GK. GK is more aggressive via fixed windows; ZBZ uses η bimodality. The methods answer different questions.

### 3.4 Threshold η0 and series detection

1. **Declustering** via Gardner–Knopoff (1974) — mainshocks for NN search.
2. **Nearest-neighbor forest:** for each event j, parent i* = argmin ηij.
3. **Threshold η0:** automatic selection from the distribution of nearest-neighbor η values. Primary method: KDE valley detection between bimodal modes in log10(η) (Zaliapin & Ben-Zion, 2013). Default cluster cut when unspecified: η0 = 10^(median log10 η). The threshold is validated against a Poisson temporal-permutation null (Monte Carlo, n = 10,000).
4. **Global series criterion:** N ≥ 4 events; M ≥ 6.5; ≥ 3 Flinn–Engdahl regions.
5. **Sliding windows** (1, 2, 5 yr; 1-yr step); overlapping groups merged.

### 3.5 Statistical validation

**ETAS null model.** To test whether series arise from local aftershock structure alone, we use global ETAS parameters (Ogata, 1988; Helmstetter & Sornette, 2003): **μ = 0.008**, **K = 0.08**, **α = 1.0**, **c = 0.005** days, **p = 1.1**; spatial triggering cutoff **500 km** (links beyond 500 km forbidden). Generation follows a branching Poisson process (≤500 km, up to 5 generations), magnitudes from Gutenberg–Richter (b = 1.0). We generate **100** synthetic catalogs (**seed = 42**) and apply the same series-detection algorithm (N ≥ 4, ≥ 3 Flinn–Engdahl regions, 2-yr window) to each. **FPR = 0/100**; **pETAS = 0.0000** (discrete test, resolution 1/101). See §5.3 for the seed limitation.

| Test | Parameters | Result |
|------|------------|--------|
| Permutation (Monte Carlo) | n = 10,000 | p < 0.0001, z = −6.17 (modern) |
| ETAS null model | μ=0.008, K=0.08, α=1.0, c=0.005 d, p=1.1; 500 km; 100 cat. | FPR = 0/100, pETAS = 0.0000 |
| FDR (Benjamini–Hochberg) | q = 0.05 | 45/47 series significant |
| Declustering | GK / ZBZ | 2,017/2,041 (24 aftersh.) / 2,040/2,041 (1 dep.) |

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

The **1905–1910** episode (193 events, 43 regions) is the largest series in the full catalog, identified in the early instrumental window. Series **S170** spans 12 Flinn–Engdahl regions and includes the 2004 Indian Ocean earthquake (M 9.1), representing the most spatially extensive modern episode (Figures 1–2 in the repository).

### 4.3 Spatial–temporal distribution

Elevated series activity occurs in 1952–1965 and 2002–2016 (post-Sumatra period). Spatially, clusters concentrate along the circum-Pacific belt (Kamchatka, Kuril Islands, Japan, Tonga, Indonesia). Tectonic distance lowers the η0 threshold by ~0.3 log10 units compared with Euclidean distance.

---

## 5. Discussion

### 5.1 Statistical anomaly vs physical mechanism

**Statistical anomaly (established):** Observed global series are incompatible with Poisson and local-only ETAS nulls (>500 km cutoff). FDR correction confirms 45/47 series. This is a conclusion about **η links and p-values**, not causality.

**Physical mechanism (not established):** The η metric is correlative; hypocentral depth, focal mechanisms, and ΔCFS are not incorporated. **Series detection does not imply direct triggering**; co-occurrence may reflect shared tectonic loading, mantle coupling, or catalog incompleteness artifacts.

**Early instrumental period (1900–1972).** Fifteen series reach p = 0.007 (z = −2.43), but quality_score < 0.7 before 1960 limits interpretation of individual episodes (including 1905–1910).

**Reconciliation with Michael (2011) and Shearer & Stark (2012).** Both tested **global event frequencies and rate trends**, not **multi-regional linkage structure**. Our η-metric detects clustering patterns largely independent of secular rate changes. The findings are complementary, not contradictory.

**Qualitative plausibility for S170.** For the post-Sumatra window 2002–2023 (S170, Mmax = 9.1), surface-wave remote-triggering literature (Hill et al., 1993; Brodsky & Prejean, 2006) provides **qualitative plausibility** for long-range correlations but not proof of causality. ΔCFS modelling and dynamic stress estimates are deferred to future work and are needed to strengthen causal claims.

Tectonic-path distance improves sensitivity (~0.3 log10 η) vs haversine; Euclidean metrics underestimate connectivity along plate boundaries.

### 5.2 Working hypotheses (not claims)

Correlative η links **do not prove** any single mechanism. Possible (unverified) explanations for long-range coupling include:

- **Viscoelastic mantle coupling** — stress redistribution over months to years after major ruptures (Pollitz et al., 1998).
- **Dynamic triggering by surface waves** — short-lived activation at thousands of kilometres (Hill et al., 1993; Brodsky & Prejean, 2006).
- **Shared tectonic loading / stress redistribution** — secular loading without direct triggering (Freed & Lin, 2001).

Co-occurrence within a series may reflect any of these (or other) processes, or catalog artifacts.

### 5.3 Limitations

**(1) Historical period:** p = 0.46; 47 M≥6.5 events pre-1900.

**⚠ (2) ETAS fixed-seed limitation (critical).** FPR = 0/100 was obtained **only at seed = 42** with 100 synthetic catalogs — a discrete outcome with 1/101 resolution. Multi-seed analysis (recommended: ≥1000 catalogs across multiple seeds) **has not been run**; ETAS robustness remains an open question. Rejecting the ETAS null **does not prove** a physical triggering mechanism. Planned: `scripts/run_etas_multiseed.py`.

**(3) Tectonic distance:** 500 km / 1.5× GC approximations; full sweep (300/500/700 km, graph resolution) is future work (§3.1).

**(4) Causality:** series ≠ direct triggering; shared loading and mantle coupling are alternative explanations.

---

## 6. Conclusions

1. A unified catalog of 4,267 M≥6.5 events (4,418 CSV records; 2150 BCE – 2026 CE) contains 47 global seismic series; 27 modern series are significant at p < 0.0001 (Monte Carlo, n = 10,000).
2. ETAS validation (μ=0.008, K=0.08, α=1.0, c=0.005 d, p=1.1, 500 km cutoff; FPR = 0/100) and FDR correction (45/47 at q = 0.05) confirm that series are not explained by randomness or local aftershock clustering alone.
3. The largest series by event count is 1905–1910 (193 events, 43 regions, Mmax = 8.8); the most spatially extensive modern series is S170 (46 events, 12 regions, 2002–2023, Mmax = 9.1).
4. Tectonic distance increases η-metric sensitivity by ~0.3 log10 units relative to Euclidean distance.
5. **Interpretive fork** (statistics vs mechanism): **(a)** if η links reflect genuine spatiotemporal structure — hazard implications and long-range ETAS kernels (without claiming direct triggering); **(b)** if episodes prove artifactual — FDR + ETAS remains a reproducible null-test pipeline. **Series detection does not imply direct triggering;** co-occurrence may reflect shared tectonic loading or mantle coupling.

**Future work:** Coulomb stress change (ΔCFS) analysis for S047, S170, and S095 incorporating **hypocentral depth and focal mechanisms** (King et al., 1994; Stein, 1999); ETAS extensions with explicit long-range kernels; Zenodo DOI release.

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
