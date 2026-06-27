# Руководство разработчика

## Быстрый запуск после клонирования

```powershell
# 1. Установка Python-зависимостей (только чистые пакеты)
pip install pandas numpy scipy networkx sqlalchemy requests tqdm scikit-learn statsmodels matplotlib plotly

# 2. Установка гео-зависимостей через conda (рекомендуется)
# conda install -c conda-forge geopandas cartopy pyproj shapely

# 3. Проверка импортов
python check_imports.py

# 4. Проверка логики алгоритмов (без внешних зависимостей)
python verify_logic.py

# 5. Запуск тестов
python -m pytest tests/ -v --tb=short
```

## Запуск всего через скрипт

```powershell
.\run_all.ps1
```

## Структура тестов

| Файл | Классы | Покрытие |
|------|--------|---------|
| `tests/test_clustering.py` | `TestEtaMetric`, `TestNearestNeighbor`, `TestIdentifyClusters`, `TestMonteCarloSignificance`, `TestEventsToTimeYears` | Метрика η, кластеризация, Monte Carlo |
| `tests/test_statistics.py` | `TestEstimateMc`, `TestInterventDistribution`, `TestSpatialExtent`, `TestMagnitudeEnergyRelease`, `TestSeriesSummaryTable` | Полнота каталога, статистика серий |
| `tests/test_curator.py` | `TestCatalogUnifier`, `TestDBManager` | Дедупликация, SQLite |

## Запуск Jupyter-ноутбуков

```bash
jupyter lab notebooks/
```

Рекомендуемый порядок:
1. `01_data_exploration.ipynb` — после сбора данных
2. `02_completeness_analysis.ipynb` — оценка полноты каталога
3. `03_clustering_demo.ipynb` — демо кластеризации (синтетические данные, работает без загрузки)
4. `04_results_visualization.ipynb` — карты и диаграммы

## Сбор реальных данных

```python
from src.curator import USGSFetcher, NOAAFetcher, ISCFetcher, CatalogUnifier
from pathlib import Path

# Загрузка USGS (занимает ~5 мин, создаёт файлы в data/raw/usgs/)
usgs = USGSFetcher()
usgs.fetch(min_magnitude=6.5, start_year=1900, end_year=2026)

# Загрузка NOAA (исторический каталог от ~2150 BCE)
noaa = NOAAFetcher()
noaa.fetch()

# Объединение
unifier = CatalogUnifier()
df = unifier.merge([usgs.to_dataframe(), noaa.to_dataframe()])
unifier.save(df, Path("data/processed/unified.csv"))
print(f"Сохранено {len(df)} событий")
```

## Полный анализ

```python
from src.analysis import SeismicClusterAnalyzer, MonteCarloTester
import pandas as pd

df = pd.read_csv("data/processed/unified.csv")

# Кластеризация
analyzer = SeismicClusterAnalyzer(df_param=1.6, b_param=1.0)
df_nn = analyzer.find_nearest_neighbor(df)
df_cl = analyzer.identify_clusters(df_nn)

# Глобальные серии
series = analyzer.global_series(df_cl, time_window_years=1.0, min_events=4)
print(f"Найдено {len(series)} глобальных серий")

# Тест значимости
tester = MonteCarloTester()
p = tester.pvalue(df_nn, n_simulations=10000)
print(f"p-value = {p:.4f}")
```

## Компиляция статьи

```bash
# Требуется LaTeX с классом agujournal2019
# https://publications.agu.org/author-resource-center/
pdflatex paper/main.tex
bibtex paper/main
pdflatex paper/main.tex
pdflatex paper/main.tex
```
