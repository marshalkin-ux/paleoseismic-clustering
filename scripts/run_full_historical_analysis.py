"""Analiz polnogo istoricheskogo kataloga s adaptirovannymi parametrami.

Tri epokhi:
  - 1973-2026: sovremennyj instrumental'nyj (time_window=2 let, min_events=4)
  - 1900-1972: rannij instrumental'nyj      (time_window=5 let, min_events=3)
  - do 1900:   istoricheskij               (time_window=50 let, min_events=3)

Dlya kazhdoj epokhi:
  1. global_series() -- kolichestvo serij
  2. MC permutation test (eta-metrika Baiesi-Paczuski)

Rezul'tat: results/analysis_full_historical.json
"""
import sys
sys.path.insert(0, '.')

import json
import logging
import time
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)

Path('results').mkdir(exist_ok=True)


# -----------------------------------------------------------------------
# MC test using eta metric (Baiesi-Paczuski 2004) -- vectorized
# -----------------------------------------------------------------------

def permutation_test_eta(
    df: pd.DataFrame,
    n_sim: int = 1000,
    seed: int = 42,
    max_sample: int = 500,
    df_param: float = 1.6,
    b_param: float = 1.0,
) -> dict:
    """
    Permutatsionnyj test znachimosti klasterizatsii po metrike eta.

    Statistika: srednee log10(eta_NN) -- chem men'she, tem sil'nee klasterizatsiya.
    H0: vremennye metki nezavisimy ot koordinat.
    p-value = P(sim_stat <= obs_stat) pod H0.
    """
    rng = np.random.default_rng(seed)

    sub = df.dropna(subset=['lat', 'lon', 'magnitude']).copy()
    if len(sub) > max_sample:
        sub = sub.sample(max_sample, random_state=seed).reset_index(drop=True)

    lats = sub['lat'].values
    lons = sub['lon'].values
    mags = sub['magnitude'].values
    year = sub['year'].fillna(0).astype(float).values
    month = sub['month'].fillna(6).astype(float).values
    day = sub['day'].fillna(15).astype(float).values
    times_orig = year + (month - 1) / 12.0 + (day - 1) / 365.25

    order = np.argsort(times_orig)
    times_orig = times_orig[order]
    lats, lons, mags = lats[order], lons[order], mags[order]

    def haversine_mat(la1, lo1, la2, lo2):
        R = 6371.0
        dlat = np.radians(la2 - la1)
        dlon = np.radians(lo2 - lo1)
        a = (np.sin(dlat / 2) ** 2
             + np.cos(np.radians(la1)) * np.cos(np.radians(la2))
             * np.sin(dlon / 2) ** 2)
        return 2 * R * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

    r_mat = haversine_mat(
        lats[:, None], lons[:, None],
        lats[None, :], lons[None, :],
    ) * 1.5

    def mean_log_eta(times: np.ndarray) -> float:
        dt = times[None, :] - times[:, None]
        mask = dt > 0
        with np.errstate(divide='ignore', invalid='ignore'):
            eta_mat = dt * (r_mat ** df_param) * (10 ** (-b_param * mags[:, None]))
        eta_mat[~mask] = np.inf
        nn_eta = eta_mat.min(axis=0)
        valid = nn_eta[np.isfinite(nn_eta) & (nn_eta > 0)]
        return float(np.mean(np.log10(valid))) if len(valid) > 0 else 0.0

    observed = mean_log_eta(times_orig)
    logger.info("Observed mean log10(eta_NN) = %.4f (n=%d used)", observed, len(sub))
    logger.info("Zapusk %d perestanovok...", n_sim)

    sim_stats = np.empty(n_sim)
    for s in range(n_sim):
        sim_stats[s] = mean_log_eta(rng.permutation(times_orig))
        if (s + 1) % 200 == 0:
            logger.info("  ... perestanovka %d/%d", s + 1, n_sim)

    valid_sim = sim_stats[~np.isnan(sim_stats)]
    n_extreme = int(np.sum(valid_sim <= observed))
    pvalue = float((n_extreme + 1) / (len(valid_sim) + 1))
    sim_mean = float(np.mean(valid_sim))
    sim_std = float(np.std(valid_sim, ddof=1))
    zscore = (observed - sim_mean) / max(sim_std, 1e-30)

    return {
        'observed_mean_log_eta': observed,
        'sim_mean': sim_mean,
        'sim_std': sim_std,
        'pvalue': pvalue,
        'zscore': float(zscore),
        'n_sim': n_sim,
        'n_events_used': len(sub),
    }


# -----------------------------------------------------------------------
# Analysis of one epoch
# -----------------------------------------------------------------------

def analyze_epoch(
    df: pd.DataFrame,
    epoch_name: str,
    time_window_years: float,
    min_events: int,
    min_regions: int = 3,
    run_mc: bool = True,
    n_sim: int = 1000,
    mc_max_sample: int = 500,
) -> dict:
    """Polnyj analiz odnoj vremennoj epokhi."""
    from src.analysis.clustering import SeismicClusterAnalyzer
    from src.analysis.etas_validation import assign_fe_regions

    logger.info("\n" + "=" * 60)
    logger.info("EPOKHA: %s (%d sobytij)", epoch_name, len(df))
    logger.info("  time_window=%.0f let, min_events=%d, min_regions=%d",
                time_window_years, min_events, min_regions)
    logger.info("=" * 60)

    result = {
        'epoch': epoch_name,
        'n_events': len(df),
        'n_events_with_magnitude': int(df['magnitude'].notna().sum()),
        'year_min': int(df['year'].min()),
        'year_max': int(df['year'].max()),
        'time_window_years': time_window_years,
        'min_events': min_events,
        'min_regions': min_regions,
    }

    if len(df) < min_events:
        logger.warning("Slishkom malo sobytij (%d) dlya analiza.", len(df))
        result['n_series'] = 0
        return result

    analyzer = SeismicClusterAnalyzer()
    df = assign_fe_regions(df)
    series_list = analyzer.global_series(
        df,
        time_window_years=time_window_years,
        min_events=min_events,
        min_magnitude=6.5,
    )
    result['min_mean_gc_km'] = 1500.0
    result['criterion'] = 'mean_pairwise_gc_km > 1500'
    # Legacy FE count stored per series; not a gate unless min_regions set
    result['min_regions'] = min_regions if min_regions is not None else 'diagnostic_only'
    result['n_series'] = len(series_list)

    series_stats = []
    for s in series_list:
        stats = {
            'n_events': len(s),
            'n_regions': int(s['fe_region'].nunique()) if 'fe_region' in s.columns else None,
            'mean_pairwise_gc_km': float(s['mean_pairwise_gc_km'].iloc[0])
            if 'mean_pairwise_gc_km' in s.columns else None,
            'year_start': int(s['year'].min()),
            'year_end': int(s['year'].max()),
            'max_magnitude': (float(s['magnitude'].max())
                               if s['magnitude'].notna().any() else None),
            'anchor_year': int(s['series_anchor_year'].iloc[0])
                           if 'series_anchor_year' in s.columns
                           else int(s['year'].iloc[0]),
        }
        series_stats.append(stats)

    series_stats.sort(key=lambda x: x['n_regions'], reverse=True)
    result['series'] = series_stats
    result['top5_series'] = series_stats[:5]

    logger.info("Najdeno serij: %d", len(series_list))
    for s in series_stats[:5]:
        logger.info("  %d-%d: %d sobytij, %d regionov, max M=%.1f",
                    s['year_start'], s['year_end'],
                    s['n_events'], s['n_regions'],
                    s['max_magnitude'] or 0)

    # Monte Carlo (eta-metric permutation test)
    if run_mc and len(df) >= 10:
        logger.info("Monte Carlo eta-metric (%d simulyacij)...", n_sim)
        t0 = time.time()
        try:
            mc = permutation_test_eta(
                df=df,
                n_sim=n_sim,
                seed=42,
                max_sample=mc_max_sample,
            )
            result['monte_carlo'] = mc
            logger.info("MC rezul'tat: p=%.4f, z=%.2f (%.0f sek)",
                        mc['pvalue'], mc['zscore'], time.time() - t0)
        except Exception as exc:
            logger.error("MC oshibka: %s", exc)
            result['monte_carlo'] = {'error': str(exc)}
    else:
        result['monte_carlo'] = {
            'skipped': True,
            'reason': 'too few events or run_mc=False',
        }

    return result


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main():
    catalog_path = Path('data/processed/unified_catalog_full.csv')
    if not catalog_path.exists():
        logger.error("Fajl ne najden: %s", catalog_path)
        logger.error("Zapustite snachala: python scripts/download_full_catalog.py")
        sys.exit(1)

    logger.info("Zagruzka kataloga: %s", catalog_path)
    df = pd.read_csv(catalog_path, low_memory=False)
    logger.info("Vsego sobytij: %d, period %d - %d",
                len(df), df['year'].min(), df['year'].max())

    df['month'] = pd.to_numeric(df['month'], errors='coerce')
    df['day'] = pd.to_numeric(df['day'], errors='coerce')
    df['magnitude'] = pd.to_numeric(df['magnitude'], errors='coerce')

    # Only events with coordinates and M>=6.5
    df_mag = df[df['magnitude'] >= 6.5].dropna(subset=['lat', 'lon']).copy()
    logger.info("Sobytij M>=6.5 s koordinatami: %d", len(df_mag))

    modern     = df_mag[df_mag['year'] >= 1973].copy()
    early      = df_mag[(df_mag['year'] >= 1900) & (df_mag['year'] < 1973)].copy()
    historical = df_mag[df_mag['year'] < 1900].copy()

    print("\n=== RAZBIRKA PO EPOHAM (M>=6.5) ===")
    print(f"  Istoricheskij (do 1900):             {len(historical)} sobytij")
    print(f"  Rannij instrumental'nyj (1900-1972): {len(early)} sobytij")
    print(f"  Sovremennyj (1973-2026):             {len(modern)} sobytij")
    print(f"  ITOGO:                               {len(df_mag)} sobytij")

    all_results = {}

    # 1. Modern period
    res_modern = analyze_epoch(
        modern, 'modern_1973_2026',
        time_window_years=2.0, min_events=4, min_regions=3,
        run_mc=True, n_sim=1000, mc_max_sample=500,
    )
    # Inject known result from existing full MC (10000 sims)
    res_modern['monte_carlo_full_10k'] = {
        'pvalue': 0.0,
        'zscore': -6.174644393457767,
        'observed_mean_log_eta': -2.8835052460518678,
        'n_sim': 10000,
        'note': 'From prior full analysis (run_full_montecarlo.py)',
    }
    all_results['modern_1973_2026'] = res_modern

    # 2. Early instrumental period
    if len(early) >= 5:
        res_early = analyze_epoch(
            early, 'early_instrumental_1900_1972',
            time_window_years=5.0, min_events=3, min_regions=3,
            run_mc=True, n_sim=1000, mc_max_sample=500,
        )
        all_results['early_instrumental_1900_1972'] = res_early
    else:
        logger.warning("Slishkom malo sobytij v rannem instrumental'nom periode: %d", len(early))
        all_results['early_instrumental_1900_1972'] = {
            'n_events': len(early), 'n_series': 0,
        }

    # 3. Historical period (pre-1900)
    if len(historical) >= 5:
        res_hist = analyze_epoch(
            historical, 'historical_pre1900',
            time_window_years=50.0, min_events=3, min_regions=2,
            run_mc=True, n_sim=500, mc_max_sample=200,
        )
        all_results['historical_pre1900'] = res_hist
    else:
        logger.warning("Slishkom malo istoricheskih sobytij: %d", len(historical))
        all_results['historical_pre1900'] = {
            'n_events': len(historical), 'n_series': 0,
        }

    # Summary
    print("\n" + "=" * 60)
    print("ITOGOVAYA STATISTIKA")
    print("=" * 60)
    for epoch_key, res in all_results.items():
        n_ev = res.get('n_events', 0)
        n_ser = res.get('n_series', 0)
        mc = res.get('monte_carlo', {})
        pval = mc.get('pvalue', 'N/A')
        zsc  = mc.get('zscore', 'N/A')
        pval_str = f"{pval:.4f}" if isinstance(pval, float) else str(pval)
        zsc_str  = f"{zsc:.2f}" if isinstance(zsc, float) else str(zsc)
        print(f"\n  {epoch_key}:")
        print(f"    Sobytij: {n_ev}  |  Serij: {n_ser}"
              f"  |  p={pval_str}  |  z={zsc_str}")

        if isinstance(pval, float):
            if pval < 0.001:
                print("    *** VYSOKO-ZNACHIMO (p < 0.001)")
            elif pval < 0.05:
                print("    **  ZNACHIMO (p < 0.05)")
            else:
                print("    --  Neznachimo (p >= 0.05)")

    # Save JSON
    def _json_default(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        try:
            if pd.isna(obj):
                return None
        except Exception:
            pass
        return str(obj)

    out_path = Path('results/analysis_full_historical.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=_json_default)
    logger.info("Sokhraneno: %s", out_path)
    print(f"\nSokhraneno: {out_path}")


if __name__ == '__main__':
    main()
