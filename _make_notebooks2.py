import json, pathlib, sys
BASE = pathlib.Path(sys.argv[1])

def nb(cells):
    return {"nbformat":4,"nbformat_minor":5,
        "metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
                    "language_info":{"name":"python","version":"3.12.0"}},
        "cells":cells}
def code(src): return {"cell_type":"code","source":src,"metadata":{},"outputs":[],"execution_count":None}
def md(src): return {"cell_type":"markdown","source":src,"metadata":{}}

nb01 = nb([
    md("# 01. Data Exploration\nLoading and initial analysis of the unified seismic catalog."),
    code("import sys\nsys.path.insert(0, '..')\nimport pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt\n%matplotlib inline"),
    code("rng = np.random.default_rng(42)\nn = 500\ndf = pd.DataFrame({\n    'event_id': [f'evt_{i}' for i in range(n)],\n    'year': rng.integers(1960, 2024, n).tolist(),\n    'year_error': [0]*n, 'month': rng.integers(1, 13, n).tolist(),\n    'day': rng.integers(1, 29, n).tolist(), 'lat': rng.uniform(-60, 60, n).tolist(),\n    'lon': rng.uniform(-180, 180, n).tolist(), 'magnitude': rng.uniform(6.5, 9.0, n).tolist(),\n    'magnitude_error': [0.1]*n, 'depth_km': rng.uniform(5, 200, n).tolist(),\n    'region': rng.choice(['Japan','Andes','Europe','Alaska'], n).tolist(),\n    'source_type': ['instrumental']*n, 'reference': ['synthetic']*n, 'quality_score': [0.9]*n,\n})\nprint(f'N events: {len(df)}')\ndf.head()"),
    code("fig, ax = plt.subplots(figsize=(12, 4))\ndf.groupby('year').size().plot(kind='bar', ax=ax, color='steelblue', alpha=0.7)\nax.set_xlabel('Year'); ax.set_ylabel('Count')\nax.set_title('Annual event count (M>=6.5)')\nplt.tight_layout(); plt.show()"),
    code("fig, ax = plt.subplots(figsize=(14, 7))\nsc = ax.scatter(df['lon'], df['lat'], c=df['magnitude'], cmap='YlOrRd',\n               s=((df['magnitude']-6)*20)**2, alpha=0.5, edgecolors='k', linewidths=0.2)\nplt.colorbar(sc, ax=ax, label='Magnitude')\nax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')\nax.set_title('Spatial distribution of events')\nax.grid(True, alpha=0.3)\nplt.tight_layout(); plt.show()"),
])

nb02 = nb([
    md("# 02. Completeness Analysis\nEstimation of Mc and b-value."),
    code("import sys\nsys.path.insert(0, '..')\nimport numpy as np\nimport pandas as pd\nimport matplotlib.pyplot as plt\nfrom src.analysis.completeness import CompletenessAnalyzer\n%matplotlib inline"),
    code("rng = np.random.default_rng(0)\nmags = 6.0 + rng.exponential(1.0 / (1.0 * np.log(10)), 1000)\ndf = pd.DataFrame({'magnitude': mags.tolist(), 'year': rng.integers(1990, 2024, len(mags)).tolist(),\n    'lat': rng.uniform(-60, 60, len(mags)).tolist(), 'lon': rng.uniform(-180, 180, len(mags)).tolist(),\n    'flinn_engdahl': 'Test-Region', 'month': 6, 'day': 15})\nanalyzer = CompletenessAnalyzer()\nmc = analyzer.estimate_mc(df)\nb, sigma = analyzer.compute_bvalue(df, mc)\nprint(f'Mc={mc:.1f}, b={b:.3f}+/-{sigma:.3f}')"),
    code("fig, ax = plt.subplots(figsize=(8, 5))\nbins = [6.0+i*0.1 for i in range(35)]\nimport numpy as np\ncounts, edges = np.histogram(df['magnitude'], bins=bins)\nax.bar(edges[:-1], counts, width=0.1, alpha=0.7, color='steelblue')\nax.axvline(mc, color='red', lw=2, linestyle='--', label=f'Mc={mc:.1f}')\nax.set_yscale('log'); ax.set_xlabel('Magnitude'); ax.set_ylabel('N')\nax.set_title(f'Gutenberg-Richter: b={b:.2f}')\nax.legend(); plt.tight_layout(); plt.show()"),
])

nb04 = nb([
    md("# 04. Results Visualization\nMaps and timelines of identified seismic series."),
    code("import sys\nsys.path.insert(0, '..')\nimport numpy as np\nimport pandas as pd\nimport matplotlib.pyplot as plt\n%matplotlib inline"),
    code("rng = np.random.default_rng(10)\ncolors = ['#1f77b4','#ff7f0e','#2ca02c']\ndef make_s(n, lc, oc, yc, sid):\n    return pd.DataFrame({\n        'year': sorted(rng.integers(yc, yc+5, n).tolist()),\n        'month': rng.integers(1, 13, n).tolist(), 'day': rng.integers(1, 28, n).tolist(),\n        'lat': (lc + rng.normal(0, 5, n)).tolist(), 'lon': (oc + rng.normal(0, 10, n)).tolist(),\n        'magnitude': rng.uniform(6.5, 8.5, n).tolist(), 'depth_km': rng.uniform(10, 100, n).tolist(),\n        'flinn_engdahl': rng.choice(['Japan-Korea','Alaska','Andes'], n).tolist(),\n        'series_id': [sid]*n,\n    })\nseries_list = [make_s(6,35,140,1995,0), make_s(5,-20,-70,2010,1), make_s(7,0,120,2004,2)]\nprint(f'Series: {len(series_list)}')"),
    code("fig, ax = plt.subplots(figsize=(14, 7))\nfor i, s in enumerate(series_list):\n    mags = s['magnitude'].values; sizes = ((mags-5)*30)**1.5\n    ax.scatter(s['lon'], s['lat'], s=sizes, c=colors[i], alpha=0.7,\n              edgecolors='k', linewidths=0.5, label=f'Series {i+1}')\nax.set_xlim(-180, 180); ax.set_ylim(-90, 90)\nax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')\nax.set_title('Global Seismic Series Map')\nax.legend(); ax.grid(True, alpha=0.3); plt.tight_layout(); plt.show()"),
    code("fig, axes = plt.subplots(len(series_list), 1, figsize=(12, 10))\nfor i, (ax, s) in enumerate(zip(axes, series_list)):\n    mags = s['magnitude'].values; years = s['year'].values\n    sizes = ((mags-5)*30)**1.5\n    ax.scatter(years, [0]*len(years), s=sizes, c=colors[i], alpha=0.8, edgecolors='k')\n    ax.axhline(0, color='gray', lw=0.8); ax.set_yticks([])\n    ax.set_xlabel('Year')\n    ax.set_title(f'Series {i+1}: {int(years.min())}-{int(years.max())}, N={len(s)}, Mmax={float(mags.max()):.1f}')\n    ax.grid(axis='x', alpha=0.3)\nplt.tight_layout(); plt.show()"),
])

for name, notebook in [("01_data_exploration",nb01),("02_completeness_analysis",nb02),("04_results_visualization",nb04)]:
    path = BASE / "notebooks" / f"{name}.ipynb"
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Written: {path.name}")
print("Done")
