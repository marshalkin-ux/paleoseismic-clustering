"""Проверка импортов всех модулей проекта."""
import sys
import traceback

results = []

modules_to_test = [
    ("src.curator.usgs_fetcher", "USGSFetcher"),
    ("src.curator.noaa_fetcher", "NOAAFetcher"),
    ("src.curator.isc_fetcher", "ISCFetcher"),
    ("src.curator.unifier", "CatalogUnifier"),
    ("src.curator.db_manager", "DBManager"),
    ("src.analysis.completeness", "CompletenessAnalyzer"),
    ("src.analysis.tectonic_distance", "TectonicDistanceCalculator"),
    ("src.analysis.clustering", "SeismicClusterAnalyzer"),
    ("src.analysis.monte_carlo", "MonteCarloTester"),
    ("src.analysis.statistics", "interevent_distribution"),
    ("src.viz.style", "apply_style"),
    ("src.viz.global_map", "plot_global_series_map"),
    ("src.viz.timelines", "plot_series_timeline"),
]

ok = 0
fail = 0
for mod, cls in modules_to_test:
    try:
        m = __import__(mod, fromlist=[cls])
        getattr(m, cls)
        results.append(f"  OK  {mod}.{cls}")
        ok += 1
    except Exception as e:
        results.append(f"  FAIL  {mod}.{cls}: {e}")
        fail += 1

print("\n".join(results))
print(f"\nРезультат: {ok} OK, {fail} FAIL")
sys.exit(0 if fail == 0 else 1)
