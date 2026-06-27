import json, pathlib, sys
import numpy as np

BASE = pathlib.Path(sys.argv[1])

def nb(cells):
    return {
        "nbformat": 4, "nbformat_minor": 5,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                     "language_info": {"name": "python", "version": "3.12.0"}},
        "cells": cells
    }
def code(src): return {"cell_type": "code", "source": src, "metadata": {}, "outputs": [], "execution_count": None}
def md(src): return {"cell_type": "markdown", "source": src, "metadata": {}}

nb01 = nb([
    md("# 01. Разведочный анализ данных\nЗагрузка и первичный анализ каталога."),
    code("import sys\nsys.path.insert(0, '..')\nimport pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\n%matplotlib inline"),
    code("rng = np.random.default_rng(42)\nn = 500\ndf = pd.DataFrame({\n    'event_id': [f'evt_{i}' for i in range(n)],\n    'year': rng.integers(1960, 2024, n),\n    'year_error': 0, 'month': rng.integers(1, 13, n),\n    'day': rng.integers(1, 29, n), 'lat': rng.uniform(-60, 60, n),\n    'lon': rng.uniform(-180, 180, n), 'magnitude': rng.uniform(6.5, 9.0, n),\n    'magnitude_error': 0.1, 'depth_km': rng.uniform(5, 200, n),\n    'region': rng.choice(['Japan-Korea','Central America','Europe','Andes','Alaska'], n),\n    'source_type': 'instrumental', 'reference': 'synthetic', 'quality_score': 0.9,\n})\nprint(f'Загружено {len(df)} событий')\ndf.head()"),
    code("fig, ax = plt.subplots(figsize=(12, 4))\ndf.groupby('year').size().plot(kind='bar', ax=ax, color='steelblue', alpha=0.7)\nax.set_xlabel('Год'); ax.set_ylabel('N событий')\nax.set_title('Временное распределение событий M>=6.5')\nplt.tight_layout(); plt.show()"),
    code("fig, ax = plt.subplots(figsize=(14, 7))\nsc = ax.scatter(df['lon'], df['lat'], c=df['magnitude'], cmap='YlOrRd',\n               s=((df['magnitude']-6)*20)**2, alpha=0.5, edgecolors='k', linewidths=0.2)\nplt.colorbar(sc, ax=ax, label='Магнитуда')\nax.set_xlabel('Долгота'); ax.set_ylabel('Широта')\nax.set_title('Пространственное распределение')\nax.grid(True, alpha=0.3)\nplt.tight_layout(); plt.show()"),
])

nb02 = nb([
    md("# 02. Анализ полноты каталога\nОценка Mc и b-value."),
    code("import sys\nsys.path.insert(0, '..')\nimport numpy as np\nimport pandas as pd\nimport matplotlib.pyplot as plt\nfrom src.analysis.completeness import CompletenessAnalyzer\n%matplotlib inline"),
    code("rng = np.random.default_rng(0)\nmags = 6.0 + rng.exponential(1.0 / (1.0 * np.log(10)), 1000)\ndf = pd.DataFrame({'magnitude': mags, 'year': rng.integers(1990, 2024, len(mags)),\n    'lat': rng.uniform(-60, 60, len(mags)), 'lon': rng.uniform(-180, 180, len(mags)),\n    'flinn_engdahl': 'Test-Region', 'month': 6, 'day': 15})\nanalyzer = CompletenessAnalyzer()\nmc = analyzer.estimate_mc(df)\nb, sigma = analyzer.compute_bvalue(df, mc)\nprint(f'Mc = {mc:.1f}, b = {b:.3f} +/- {sigma:.3f}')"),
    code("fig, ax = plt.subplots(figsize=(8, 5))\nbins = np.arange(6.0, 9.5, 0.1)\ncounts, edges = np.histogram(df['magnitude'], bins=bins)\nax.bar(edges[:-1], counts, width=0.1, alpha=0.7, color='steelblue')\nax.axvline(mc, color='red', lw=2, linestyle='--', label=f'Mc = {mc:.1f}')\nax.set_yscale('log'); ax.set_xlabel('Магнитуда'); ax.set_ylabel('N')\nax.set_title(f'ЧМХ Гутенберга-Рихтера: b = {b:.2f}')\nax.legend(); plt.tight_layout(); plt.show()"),
])

nb04 = nb([
    md("# 04. Визуализация результатов\nКарты и временные шкалы сейсмических серий."),
    code("import sys\nsys.path.insert(0, '..')\nimport numpy as np\nimport pandas as pd\nimport matplotlib.pyplot as plt\n%matplotlib inline"),
    code("rng = np.random.default_rng(10)\ncolors = ['#1f77b4','#ff7f0e','#2ca02c']\ndef make_series(n, lat_c, lon_c, year_c, sid):\n    return pd.DataFrame({\n        'year': np.sort(rng.integers(year_c, year_c+5, n)),\n        'month': rng.integers(1, 13, n), 'day': rng.integers(1, 28, n),\n        'lat': lat_c + rng.normal(0, 5, n), 'lon': lon_c + rng.normal(0, 10, n),\n        'magnitude': rng.uniform(6.5, 8.5, n), 'depth_km': rng.uniform(10, 100, n),\n        'flinn_engdahl': rng.choice(['Japan-Korea','Alaska','Central America'], n),\n        'series_id': sid,\n    })\nseries_list = [make_series(6, 35, 140, 1995, 0),\n               make_series(5, -20, -70, 2010, 1),\n               make_series(7, 0, 120, 2004, 2)]\nprint(f'Серий: {len(series_list)}')"),
    code("fig, ax = plt.subplots(figsize=(14, 7))\nfor i, s in enumerate(series_list):\n    mags = s['magnitude'].values; sizes = ((mags-5)*30)**1.5\n    ax.scatter(s['lon'], s['lat'], s=sizes, c=colors[i], alpha=0.7,\n              edgecolors='k', linewidths=0.5, label=f'Series {i+1}')\nax.set_xlim(-180, 180); ax.set_ylim(-90, 90)\nax.set_xlabel('Lon'); ax.set_ylabel('Lat')\nax.set_title('Global Seismic Series')\nax.legend(); ax.grid(True, alpha=0.3)\nplt.tight_layout(); plt.show()"),
])

for name, notebook in [("01_data_exploration", nb01), ("02_completeness_analysis", nb02), ("04_results_visualization", nb04)]:
    path = BASE / "notebooks" / f"{name}.ipynb"
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Written: {path.name}")
print("Done")

