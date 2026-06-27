# 05. Быстрый старт

Этот раздел проведёт вас от установки до получения первых результатов анализа глобальных сейсмических серий.

---

## 5.1 Установка

### Требования

- Python **3.10** или выше
- ~4 GB свободного места (данные каталогов + граф разломов)
- Git

### Вариант A: pip (Linux / macOS)

```bash
git clone https://github.com/marshalkin-ux/paleoseismic-clustering.git
cd paleoseismic-clustering
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Вариант B: conda (рекомендуется для Windows)

Пакет **Cartopy** (используется для картографической визуализации) на Windows крайне сложно установить через pip из-за зависимостей от GEOS/PROJ. Используйте conda:

```bash
git clone https://github.com/marshalkin-ux/paleoseismic-clustering.git
cd paleoseismic-clustering

conda create -n paleoseismic python=3.11 -y
conda activate paleoseismic

# Cartopy и GDAL через conda-forge
conda install -c conda-forge cartopy gdal proj -y

# Остальные зависимости через pip
pip install -r requirements.txt --ignore-installed cartopy
```

> **Известная проблема на Windows**: если при `import cartopy` возникает `DLL load failed`, выполните `conda install -c conda-forge vs2015_runtime` и перезапустите среду.

---

## 5.2 Загрузка данных

### USGS ComCat

```python
from fetchers.usgs import USGSFetcher
from pathlib import Path

usgs = USGSFetcher(
    min_magnitude=5.0,
    start_year=1960,
    end_year=2024,
    chunk_years=5,
    output_dir=Path("data/raw/usgs"),
)
usgs_df = usgs.fetch_all()
print(f"USGS: загружено {len(usgs_df)} событий")
```

### NOAA NGDC

```python
from fetchers.noaa import NOAAFetcher

noaa = NOAAFetcher(
    min_magnitude=6.0,
    min_year=1900,
    max_year=2024,
    min_quality_score=2,
    output_path=Path("data/raw/noaa/noaa_catalog.json"),
)
noaa_df = noaa.fetch_all()
print(f"NOAA: загружено {len(noaa_df)} событий")
```

### ISC Bulletin (предзагруженный CSV)

Файл ISC необходимо запросить вручную на [isc.ac.uk](http://www.isc.ac.uk/iscbulletin/search/bulletin/) и сохранить в `data/raw/isc/isc_bulletin.csv`.

```python
from fetchers.isc import ISCFetcher

isc = ISCFetcher(
    csv_path=Path("data/raw/isc/isc_bulletin.csv"),
    min_magnitude=5.0,
)
isc_df = isc.load()
print(f"ISC: загружено {len(isc_df)} событий")
```

---

## 5.3 Объединение каталогов

```python
from unifier.catalog import CatalogUnifier

unifier = CatalogUnifier(
    spatial_threshold_km=50.0,
    temporal_threshold_days=30.0,
)
unifier.add_catalog(isc_df, source="isc")
unifier.add_catalog(usgs_df, source="usgs")
unifier.add_catalog(noaa_df, source="noaa")

unified_df = unifier.unify()
print(f"Унифицированный каталог: {len(unified_df)} событий")

# Сохранение
unified_df.to_csv("data/unified_catalog.csv", index=False)

# Сохранение в SQLite
from db.manager import DBManager
db = DBManager(db_path=Path("data/seismic_catalog.db"))
db.init_schema()
n_inserted = db.insert_events(unified_df)
print(f"Вставлено в БД: {n_inserted} записей")
```

---

## 5.4 Анализ полноты

```python
from analysis.completeness import CompletenessAnalyzer

# Работаем с событиями M >= 5.0
analyzer = CompletenessAnalyzer(
    catalog=unified_df[unified_df["magnitude"] >= 5.0],
    mag_bin=0.1,
)

mc = analyzer.estimate_mc(method="maxc")
b, sigma_b = analyzer.estimate_b_value(mc=mc)
print(f"Mc = {mc:.1f}, b = {b:.3f} ± {sigma_b:.3f}")

# Матрица полноты по ключевым регионам
from viz.completeness import plot_fmd
fig = plot_fmd(unified_df, mc=mc, b=b, output_path=Path("output/fmd.png"))
```

---

## 5.5 Поиск глобальных серий

```python
from analysis.tectonic_distance import TectonicDistanceCalculator
from analysis.clustering import SeismicClusterAnalyzer
from statistics import get_eta_threshold

# Вычисление тектонических расстояний (затратная операция — кэшируется)
tdist = TectonicDistanceCalculator(
    gem_faults_path=Path("data/gem_active_faults.geojson"),
    bird_plates_path=Path("data/bird2003_plates.geojson"),
    cache_path=Path("data/distance_cache.npz"),
)
catalog_large = unified_df[unified_df["magnitude"] >= 6.5].reset_index(drop=True)
dist_matrix = tdist.compute_distance_matrix(catalog_large)

# η-анализ
cluster_analyzer = SeismicClusterAnalyzer(
    catalog=catalog_large,
    distance_matrix=dist_matrix,
    b_value=b,
    df=1.6,
)
eta_matrix = cluster_analyzer.compute_eta_matrix()
eta_threshold = get_eta_threshold(eta_matrix, percentile=5.0)

series = cluster_analyzer.find_global_series(
    eta_threshold=eta_threshold,
    window_years=1.0,
    min_events=4,
    min_magnitude=6.5,
    min_fe_regions=3,
)
print(f"Обнаружено глобальных серий: {len(series)}")
```

---

## 5.6 Монте-Карло тест

```python
from analysis.montecarlo import MonteCarloTester

tester = MonteCarloTester(
    analyzer=cluster_analyzer,
    n_simulations=1000,
    random_seed=42,
)
mc_results = tester.run(observed_series=series)

print(f"p-value = {mc_results['p_value']:.4f}")
print(f"Наблюдаемых серий: {mc_results['n_observed']}")
print(f"95% CI нулевого распределения: {mc_results['confidence_interval']}")
```

---

## 5.7 Визуализация результатов

```python
from viz.maps import plot_series_map
from viz.dendrograms import plot_eta_dendrogram
from pathlib import Path

output_dir = Path("output/figures")
output_dir.mkdir(parents=True, exist_ok=True)

# Карта первой обнаруженной серии
if series:
    fig_map = plot_series_map(
        series=series[0],
        catalog=catalog_large,
        output_path=output_dir / "series_map.png",
    )

# η-дендрограмма
fig_dendro = plot_eta_dendrogram(
    eta_matrix=eta_matrix,
    catalog=catalog_large,
    output_path=output_dir / "eta_dendrogram.png",
)

print("Визуализации сохранены в output/figures/")
```

---

## 5.8 Полный сквозной пример

```python
"""
Полный пример анализа глобальных сейсмических серий (1960–2024, M >= 6.5).
Запуск: python run_analysis.py
"""
from pathlib import Path
import pandas as pd

from fetchers.usgs import USGSFetcher
from fetchers.isc import ISCFetcher
from unifier.catalog import CatalogUnifier
from db.manager import DBManager
from analysis.completeness import CompletenessAnalyzer
from analysis.tectonic_distance import TectonicDistanceCalculator
from analysis.clustering import SeismicClusterAnalyzer
from analysis.montecarlo import MonteCarloTester
from statistics import get_eta_threshold
from viz.maps import plot_series_map
from viz.dendrograms import plot_eta_dendrogram
from viz.completeness import plot_fmd

DATA_DIR = Path("data")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# 1. Загрузка данных
print("[1/7] Загрузка данных...")
usgs_df = USGSFetcher(min_magnitude=5.0, start_year=1960, end_year=2024).fetch_all()
isc_df = ISCFetcher(DATA_DIR / "raw/isc/isc_bulletin.csv").load()

# 2. Унификация
print("[2/7] Унификация каталогов...")
unifier = CatalogUnifier(spatial_threshold_km=50.0, temporal_threshold_days=30.0)
unifier.add_catalog(isc_df, source="isc")
unifier.add_catalog(usgs_df, source="usgs")
unified_df = unifier.unify()
unified_df.to_csv(DATA_DIR / "unified_catalog.csv", index=False)

# 3. БД
db = DBManager(DATA_DIR / "seismic_catalog.db")
db.init_schema()
db.insert_events(unified_df)

# 4. Полнота
print("[3/7] Анализ полноты...")
comp = CompletenessAnalyzer(unified_df[unified_df["magnitude"] >= 5.0])
mc = comp.estimate_mc(method="maxc")
b, sigma_b = comp.estimate_b_value(mc=mc)
plot_fmd(unified_df, mc=mc, b=b, output_path=OUTPUT_DIR / "fmd.png")
print(f"    Mc = {mc:.1f}, b = {b:.3f} +/- {sigma_b:.3f}")

# 5. Тектонические расстояния
print("[4/7] Граф разломов и матрица расстояний...")
catalog_large = unified_df[unified_df["magnitude"] >= 6.5].reset_index(drop=True)
tdist = TectonicDistanceCalculator(
    gem_faults_path=DATA_DIR / "gem_active_faults.geojson",
    bird_plates_path=DATA_DIR / "bird2003_plates.geojson",
    cache_path=DATA_DIR / "distance_cache.npz",
)
dist_matrix = tdist.compute_distance_matrix(catalog_large)

# 6. Поиск серий
print("[5/7] Вычисление eta и поиск серий...")
analyzer = SeismicClusterAnalyzer(catalog_large, dist_matrix, b_value=b, df=1.6)
eta_matrix = analyzer.compute_eta_matrix()
eta_threshold = get_eta_threshold(eta_matrix, percentile=5.0)
series = analyzer.find_global_series(eta_threshold=eta_threshold, min_events=4,
                                     min_magnitude=6.5, min_fe_regions=3)
db.save_series(series)
print(f"    Найдено серий: {len(series)}")

# 7. Monte Carlo + визуализация
print("[6/7] Монте-Карло тест (1000 симуляций)...")
mc_res = MonteCarloTester(analyzer, n_simulations=1000).run(series)
print(f"    p-value = {mc_res['p_value']:.4f}")

print("[7/7] Визуализация...")
if series:
    plot_series_map(series[0], catalog_large, OUTPUT_DIR / "series_map.png")
plot_eta_dendrogram(eta_matrix, catalog_large, OUTPUT_DIR / "eta_dendrogram.png")

print("Готово! Результаты в папке output/")
```