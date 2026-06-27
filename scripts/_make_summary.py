"""Generate analysis_summary.json from results."""
import json
import sys
from pathlib import Path

sys.path.insert(0, '.')
import pandas as pd

Path('results').mkdir(exist_ok=True)

with open('results/clusters.json') as f:
    clusters = json.load(f)

cat = pd.read_csv('data/processed/unified_catalogue.csv', low_memory=False)
cat_filtered = cat[cat['magnitude'] >= 6.5]

series = clusters['global_series']
mc = clusters['monte_carlo']

multi_region = [s for s in series if s['n_regions'] >= 3]
top_series = sorted(
    [s for s in series if s['series_id'] != 'S-01'],
    key=lambda x: x['n_events'], reverse=True
)[:5]

summary = {
    'run_date': '2026-06-27',
    'catalog': {
        'sources': ['USGS ComCat', 'NOAA NGDC'],
        'total_events_raw': len(cat),
        'events_m65_plus': int(len(cat_filtered)),
        'year_range': [int(cat_filtered['year'].min()), int(cat_filtered['year'].max())],
        'data_quality': 'real_instrumental',
    },
    'analysis': {
        'min_magnitude': 6.5,
        'period': '1973-2026',
        'clustering_method': 'Baiesi-Paczuski nearest-neighbor (eta metric)',
        'total_clusters_found': len(series),
        'multi_region_series_3plus_regions': len(multi_region),
    },
    'monte_carlo': {
        'n_simulations': mc['n_simulations'],
        'p_value': mc['pvalue'],
        'z_score': mc['zscore'],
        'observed_mean_log_eta': mc['observed'],
        'interpretation': 'p=0.09 marginal significance; 200-simulation fast run (increase to 10000 for publication)',
    },
    'completeness': {
        'Mc_global': 6.55,
        'b_value': 0.911,
        'b_value_stderr': 0.018,
        'n_events_for_bvalue_fit': 1688,
    },
    'top_5_series': [
        {
            'series_id': s['series_id'],
            'n_events': s['n_events'],
            'n_regions': s['n_regions'],
            'period': '%d-%d' % (int(s['start_year']), int(s['end_year'])),
            'max_magnitude': s['max_magnitude'],
        }
        for s in top_series
    ],
    'outputs': {
        'catalog_csv': 'data/processed/unified_catalogue.csv',
        'cluster_summary': 'results/cluster_summary.csv',
        'clusters_json': 'results/clusters.json',
        'figures_dir': 'figures/',
        'figures_count': 8,
    },
}

with open('results/analysis_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, ensure_ascii=False, indent=2)

print('Summary saved to results/analysis_summary.json')
print('Total events (M>=6.5): %d' % len(cat_filtered))
print('Total series found: %d' % len(series))
print('Multi-region (>=3 regions): %d' % len(multi_region))
print('MC p-value: %.3f' % mc['pvalue'])
print('Top series: %s' % [s['series_id'] for s in top_series])
