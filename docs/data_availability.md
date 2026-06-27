# Data and Code Availability

**Repository:** [github.com/marshalkin-ux/paleoseismic-clustering](https://github.com/marshalkin-ux/paleoseismic-clustering)  
**Catalog:** `data/processed/unified_catalog_full.csv` (4,418 rows; **4,267** unique M≥6.5 after dedup)  
**Interactive demo:** [marshalkin-ux.github.io/paleoseismic-clustering](https://marshalkin-ux.github.io/paleoseismic-clustering/)

## Merged catalog

| Artifact | Description |
|----------|-------------|
| `data/processed/unified_catalog_full.csv` | 4,418 saved CSV rows (includes ~151 NOAA events with M 6.0–6.4 from M≥6.0 fetch) |
| After M≥6.5 filter + dedup | **4,267** unique events (±30 days, ≤50 km; ISC > USGS > NOAA) |

### Catalog merge reconciliation

| Stage | Count | Notes |
|-------|------:|-------|
| CSV rows saved | 4,418 | Includes ~151 events M<6.5 from NOAA (M≥6.0 fetch) |
| Unique M≥6.5 after dedup | 4,267 | ±30 d, ≤50 km |
| USGS ComCat raw (1973–2026) | 2,088 | Legacy instrumental window |
| Modern merged (1973–2026) | 2,041 | After ISC/NOAA merge and dedup |
| GK mainshocks (modern) | 2,017 | ~24 aftershocks removed (98.8%) |
| ZBZ independent (modern) | 2,040 | 1 dependent event (100.0%); sensitivity check |

## Analysis outputs

| File | Contents |
|------|----------|
| `results/analysis_full_historical.json` | Full historical series detection summary |
| `results/etas_validation.json` | ETAS null-model validation (100 catalogs, seed=42) |
| `results/fdr_correction_results.csv` | Benjamini–Hochberg FDR per-series q-values |
| `results/montecarlo_full.json` | Permutation-test null distribution |
| `results/clusters.json` | Identified global series metadata |
| `results/cluster_summary.csv` | Series-level summary table |

## Figures

| Path | Description |
|------|-------------|
| `figures/grl/fig01_global_map.png` | Global map of identified series |
| `figures/grl/fig02_etas_validation.png` | ETAS null-model histogram |
| `figures/grl/fig05_tectonic_vs_euclidean.png` | Tectonic vs Euclidean η sensitivity |
| `figures/viz2_eta_distribution.png` | Nearest-neighbor η distribution |

## Reproducing results

```bash
pip install -r requirements.txt
python scripts/run_etas_validation.py
python scripts/apply_fdr_correction.py
python scripts/generate_grl_figures.py
python scripts/generate_article_pdf.py
python scripts/generate_article_en_pdf.py
```

See [docs/05_quickstart.md](05_quickstart.md) for the full pipeline.
