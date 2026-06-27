# Manual Data Import Instructions

Some paleoseismological and archaeoseismological catalogues are not available
via public APIs and must be obtained from publishers or personal contact with
authors.  The following datasets should be manually placed in this directory
in CSV or Excel format before running `scripts/download_data.py`.

---

## 1. Ambraseys Historical Catalogues

- **Source:** Ambraseys, N.N. & Melville, C.P. (1994). *A History of Persian
  Earthquakes.* Cambridge University Press.
- **Regions:** Middle East, Central Asia
- **Period:** ~0–1900 CE
- **Expected filename:** `ambraseys_persian_eq.csv`
- **Required columns:** year, year_error, lat, lon, magnitude, mag_type, location

## 2. Guidoboni Mediterranean Catalogue

- **Source:** Guidoboni, E. & Comastri, A. (2005). *Catalogue of Earthquakes
  and Tsunamis in the Mediterranean Area from the 11th to the 15th Century.*
  INGV-SGA, Bologna.
- **Regions:** Mediterranean Basin
- **Period:** 1000–1500 CE
- **Expected filename:** `guidoboni_mediterranean_eq.csv`

## 3. ISC-GEM Pre-1900 Extension

- **Source:** Albini, P. et al. (2013). Global historical earthquake archive
  and catalogue (1000–1903). *Annals of Geophysics*, 56, G0447.
- **Download:** https://www.emidius.eu/AHEAD/
- **Expected filename:** `iscgem_pre1900.csv`

## 4. Paleoseismological Trench Databases

Individual paleoseismic event records from published trench studies can be
added as separate CSV files with the following naming convention:
`paleo_[region]_[year_of_publication].csv`

Minimum required columns:
- `year`          (negative = BCE)
- `year_error`    (±1σ in years)
- `lat`, `lon`
- `magnitude`     (estimated from rupture length or displacement)
- `magnitude_error`
- `reference`     (full citation)

---

## Unified import

After placing files here, run:

```bash
python scripts/download_data.py --manual-import data/raw/
```

The manual-import flag instructs the curator to scan for CSV files and
attempt to normalise them using the `normalize_manual()` function in
`src/curator/normalizer.py`.
