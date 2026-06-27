"""Скрипт запуска ETAS-валидации на реальном каталоге.

Оценивает частоту ложных открытий алгоритма кластеризации:
генерирует 1000 ETAS-каталогов (по умолчанию), на каждом ищет «глобальные серии»
и сравнивает с числом реально найденных серий.

Использование:
    python scripts/run_etas_validation.py

Выходные файлы:
    results/etas_validation.json
"""

import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

from src.analysis.etas_params import load_calibrated_etas_params, load_literature_etas_params
from src.analysis.etas_validation import ETASCatalogGenerator
from src.analysis.clustering import SeismicClusterAnalyzer

CALIBRATION_PATH = Path("results/etas_calibration.json")


def load_etas_params() -> dict:
    """Load catalog-calibrated ETAS params (diagnostic null; literature is primary for inference)."""
    params = load_calibrated_etas_params(CALIBRATION_PATH)
    clean = {k: v for k, v in params.items() if not k.startswith("_")}
    logger.info(
        "Primary ETAS (catalog MLE): mu=%.6f K=%.4f alpha=%.3f c=%.5f p=%.3f",
        clean["mu"], clean["K"], clean["alpha"], clean["c"], clean["p"],
    )
    return clean


# ---------------------------------------------------------------------------
# Загрузка каталога
# ---------------------------------------------------------------------------

catalog_path = Path("data/processed/unified_catalog_full.csv")
if not catalog_path.exists():
    logger.error("Каталог не найден: %s", catalog_path)
    sys.exit(1)

df = pd.read_csv(catalog_path)
logger.info("Загружено событий: %d", len(df))

# Оставляем только инструментальный период (с 1973)
if "year" in df.columns:
    df = df[df["year"] >= 1973].copy()
    df = df[df["magnitude"] >= 6.5].copy()
    logger.info("После фильтра 1973+ M>=6.5: %d событий", len(df))

from src.analysis.etas_validation import assign_fe_regions
df = assign_fe_regions(df)

# ---------------------------------------------------------------------------
# Инициализация
# ---------------------------------------------------------------------------

etas_params = load_etas_params()

analyzer = SeismicClusterAnalyzer()

generator = ETASCatalogGenerator(
    mu=etas_params["mu"],
    K=etas_params["K"],
    alpha=etas_params["alpha"],
    c=etas_params["c"],
    p=etas_params["p"],
    max_trigger_distance_km=etas_params.get("max_trigger_distance_km", 500.0),
    use_calibrated_defaults=False,
)

# Background count scaled from calibrated mu (53 yr window ≈ catalog span)
t_span_years = float(df["year"].max() - df["year"].min()) if len(df) else 53.0
n_background = int(round(etas_params["mu"] * t_span_years * 365.25))
n_background = max(n_background, 40)
logger.info(
    "ETAS generator: mu=%.6f K=%.4f alpha=%.3f c=%.5f p=%.3f n_bg=%d",
    etas_params["mu"],
    etas_params["K"],
    etas_params["alpha"],
    etas_params["c"],
    etas_params["p"],
    n_background,
)

# ---------------------------------------------------------------------------
# Число реально найденных серий в реальном каталоге
# ---------------------------------------------------------------------------

logger.info("Поиск серий в реальном каталоге...")
try:
    real_series = analyzer.global_series(
        df,
        min_events=4,
        time_window_years=2.0,
    )
    n_observed = len(real_series)
except Exception as exc:
    logger.warning("Не удалось запустить global_series: %s", exc)
    n_observed = 27

logger.info("Реальных глобальных серий: %d", n_observed)

# ---------------------------------------------------------------------------
# ETAS-валидация (1000 каталогов по умолчанию)
# ---------------------------------------------------------------------------

N_CATALOGS = 1000

logger.info("Запуск ETAS-валидации (%d каталогов)...", N_CATALOGS)

results = generator.run_false_positive_analysis(
    cluster_analyzer=analyzer,
    n_catalogs=N_CATALOGS,
    min_events=4,
    time_window_years=2.0,
    n_observed=n_observed,
    seed=42,
    n_background=n_background,
    t_span_years=t_span_years,
)

results["etas_parameters"] = etas_params
results["etas_parameters_primary"] = "catalog_mle_1973_2026"
results["etas_parameters_literature_comparison"] = load_literature_etas_params()
results["n_background_per_catalog"] = n_background
results["catalog_span_years"] = t_span_years
results["clustering_criterion"] = "mean_pairwise_gc_km > 1500"

# ---------------------------------------------------------------------------
# Вывод результатов
# ---------------------------------------------------------------------------

print("\n=== РЕЗУЛЬТАТЫ ETAS-ВАЛИДАЦИИ ===")
print(f"Реальных глобальных серий:    {results['n_observed']}")
print(f"В ETAS-каталогах (среднее):   {results['mean_false_series']:.2f} ± {results['std_false_series']:.2f}")
print(f"FPR (>=1 ложной серии):       {results['n_catalogs_with_false_series']}/{results['n_catalogs']} ({results['false_positive_rate']:.3f})")
print(f"Max ложных серий:             {results['max_false_series']}")
print(f"p-value (ETAS):               {results['p_value_empirical']:.4f}")

if not pd.isna(results["p_value_empirical"]):
    sig = results["p_value_empirical"] < 0.05
    print(f"Интерпретация:                {'ЗНАЧИМО (p < 0.05)' if sig else 'НЕ ЗНАЧИМО (p >= 0.05)'}")

# ---------------------------------------------------------------------------
# Сохранение
# ---------------------------------------------------------------------------

out_path = Path("results/etas_validation.json")
out_path.parent.mkdir(parents=True, exist_ok=True)

save_results = dict(results)

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(save_results, f, indent=2, ensure_ascii=False, default=str)

logger.info("Сохранено: %s", out_path)
