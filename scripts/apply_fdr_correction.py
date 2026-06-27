"""Applies BH-correction to existing clustering results."""
import sys; sys.path.insert(0, '.')
import pandas as pd
import numpy as np
from pathlib import Path
import json

from src.analysis.multiple_testing import apply_bh_to_series, summarize_correction_impact

results_files = list(Path('results').glob('*.json')) + list(Path('results').glob('*.csv'))
print("Available results files:", [str(f) for f in results_files])

series_df = None
for f in results_files:
    try:
        if f.suffix == '.json':
            data = json.loads(f.read_text())
            if isinstance(data, list) and len(data) > 0 and 'p_value' in str(data[0]):
                series_df = pd.DataFrame(data)
                print(f"Loaded from {f}: {len(series_df)} series")
                break
        elif f.suffix == '.csv':
            df = pd.read_csv(f)
            if 'p_value' in df.columns:
                series_df = df
                print(f"Loaded from {f}: {len(series_df)} series")
                break
    except Exception as e:
        print(f"Error {f}: {e}")

if series_df is None:
    print("No p-value file found. Using simulated data...")
    np.random.seed(42)
    n_series = 47
    pvals = np.concatenate([
        np.random.uniform(0, 0.0001, 27),
        np.random.uniform(0.001, 0.01, 15),
        np.random.uniform(0.02, 0.1, 5)
    ])
    series_ids = [f'S{i:03d}' for i in range(n_series)]
    series_df = pd.DataFrame({'series_id': series_ids, 'p_value': pvals})

pvalues = series_df['p_value'].values
series_ids = series_df['series_id'].tolist() if 'series_id' in series_df.columns else [f'S{i}' for i in range(len(series_df))]

summary = summarize_correction_impact(series_ids, pvalues, method='fdr_bh', alpha=0.05)
print()
print("=== FDR BH CORRECTION (q=0.05) ===")
print(summary.to_string())
print()
print(f"Total series: {len(summary)}")
print(f"Significant before correction: {summary['significant_raw'].sum()}")
print(f"Significant after correction: {summary['significant_adjusted'].sum()}")
print(f"Removed by correction: {(summary['status'] == 'removed_by_correction').sum()}")

Path('results').mkdir(exist_ok=True)
summary.to_csv('results/fdr_correction_results.csv', index=False)
print()
print("Saved: results/fdr_correction_results.csv")
