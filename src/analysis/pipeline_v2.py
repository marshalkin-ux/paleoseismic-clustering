"""Улучшенный пайплайн с декластеризацией, FDR и ETAS-валидацией.

Воспроизводимый end-to-end анализ глобальных сейсмических серий
с полным набором улучшений:

1. Загрузка и предобработка каталога.
2. Декластеризация (Gardner-Knopoff или Zaliapin-Ben-Zion).
3. Анализ полноты каталога.
4. Кластеризация (η NN forest; series gate = great-circle only).
5. Monte Carlo тест значимости.
6. FDR коррекция p-value.
7. ETAS валидация (оценка частоты ложных открытий).
8. Сохранение результатов.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def _load_catalog(path: str) -> pd.DataFrame:
    """Загружает каталог из CSV или Parquet.

    Args:
        path: путь к файлу (CSV или Parquet).

    Returns:
        DataFrame каталога.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Файл каталога не найден: {path}")

    suffix = p.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path)
    elif suffix in (".parquet", ".pq"):
        df = pd.read_parquet(path)
    else:
        raise ValueError(f"Неподдерживаемый формат файла: {suffix}")

    logger.info("Загружен каталог: %d событий из %s", len(df), path)
    return df


def _ensure_output_dir(output_dir: str) -> Path:
    """Создаёт директорию вывода при необходимости."""
    p = Path(output_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _save_results(results: dict, output_dir: Path) -> None:
    """Сохраняет результаты анализа в файлы."""
    # Основные серии
    if "series" in results and results["series"]:
        all_series = []
        for i, s in enumerate(results["series"]):
            s_copy = s.copy()
            s_copy["series_id"] = i
            all_series.append(s_copy)
        pd.concat(all_series, ignore_index=True).to_csv(
            output_dir / "series_v2.csv", index=False,
        )

    # FDR таблица
    if "fdr_table" in results and results["fdr_table"] is not None:
        results["fdr_table"].to_csv(output_dir / "fdr_results_v2.csv", index=False)

    # Декластеризованный каталог
    if "declustered_catalog" in results:
        results["declustered_catalog"].to_csv(
            output_dir / "declustered_catalog.csv", index=False,
        )

    # Метаданные
    meta = {
        k: v for k, v in results.items()
        if not isinstance(v, (pd.DataFrame, list, np.ndarray))
    }
    with open(output_dir / "pipeline_v2_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2, default=str)

    logger.info("Результаты сохранены в %s", output_dir)


# ---------------------------------------------------------------------------
# Основная функция пайплайна
# ---------------------------------------------------------------------------

def run_full_analysis(
    catalog_path: str,
    output_dir: str,
    decluster: bool = True,
    decluster_method: str = "gardner_knopoff",
    apply_fdr: bool = True,
    time_window_years: float = 1.0,
    min_events: int = 4,
    min_regions: int = 3,
    min_magnitude: float = 6.5,
    n_monte_carlo: int = 10000,
    run_etas_validation: bool = False,
    n_etas_catalogs: int = 100,
    use_tectonic_v2: bool = True,
) -> dict:
    """Полный воспроизводимый пайплайн анализа.

    Args:
        catalog_path: путь к CSV/Parquet файлу каталога.
        output_dir: директория для сохранения результатов.
        decluster: применять ли декластеризацию.
        decluster_method: ``'gardner_knopoff'`` или ``'zaliapin'``.
        apply_fdr: применять ли FDR коррекцию p-value.
        time_window_years: размер временно́го окна для поиска серий (лет).
        min_events: минимальное число событий в серии.
        min_regions: минимальное число регионов в серии.
        min_magnitude: минимальная магнитуда для анализа.
        n_monte_carlo: число итераций Monte Carlo.
        run_etas_validation: выполнять ли ETAS-валидацию.
        n_etas_catalogs: число синтетических каталогов для ETAS.
        use_tectonic_v2: **deprecated diagnostic** — Bird-graph distance for η NN forest
            only; not used in ``global_series()`` gates or reported N_obs.

    Returns:
        Словарь с результатами::

            {
                'n_total': int,
                'n_after_declustering': int,
                'n_series': int,
                'series': list[pd.DataFrame],
                'p_values': dict[str, float],
                'fdr_table': pd.DataFrame | None,
                'etas_validation': dict | None,
                'declustered_catalog': pd.DataFrame,
                'elapsed_sec': float,
            }
    """
    t0 = time.time()
    out_dir = _ensure_output_dir(output_dir)
    results: dict[str, Any] = {}

    # -----------------------------------------------------------------------
    # Шаг 1: Загрузка каталога
    # -----------------------------------------------------------------------
    logger.info("=== Шаг 1: Загрузка каталога ===")
    df = _load_catalog(catalog_path)
    results["n_total"] = len(df)

    # Фильтрация по магнитуде
    df = df[df["magnitude"] >= min_magnitude].copy().reset_index(drop=True)
    logger.info("После фильтрации M>=%.1f: %d событий", min_magnitude, len(df))

    # -----------------------------------------------------------------------
    # Шаг 2: Декластеризация (опционально)
    # -----------------------------------------------------------------------
    if decluster:
        logger.info("=== Шаг 2: Декластеризация (%s) ===", decluster_method)
        from .declustering import GardnerKnopoffDeclustering, ZaliaipinDeclustering

        if decluster_method == "gardner_knopoff":
            dec = GardnerKnopoffDeclustering()
            df_main, df_dep = dec.decluster(df)
        elif decluster_method == "zaliapin":
            dec = ZaliaipinDeclustering()
            df_main, df_dep = dec.decluster(df)
        else:
            raise ValueError(f"Неизвестный метод декластеризации: {decluster_method!r}")

        df_analysis = df_main.copy()
        logger.info(
            "Декластеризация: %d главных толчков, %d зависимых",
            len(df_main), len(df_dep),
        )
    else:
        logger.info("=== Шаг 2: Декластеризация пропущена ===")
        df_analysis = df.copy()

    results["n_after_declustering"] = len(df_analysis)
    results["declustered_catalog"] = df_analysis

    # -----------------------------------------------------------------------
    # Шаг 3: Анализ полноты
    # -----------------------------------------------------------------------
    logger.info("=== Шаг 3: Анализ полноты ===")
    try:
        from .completeness import CompletenessAnalyzer
        comp = CompletenessAnalyzer()
        mc = comp.estimate_mc(df_analysis)
        b_val, b_std = comp.compute_bvalue(df_analysis, mc)
        results["mc"] = float(mc)
        results["b_value"] = float(b_val)
        results["b_std"] = float(b_std)
        logger.info("Mc=%.1f, b=%.2f±%.2f", mc, b_val, b_std)
    except Exception as exc:
        logger.warning("Анализ полноты не выполнен: %s", exc)
        results["mc"] = min_magnitude
        results["b_value"] = 1.0
        results["b_std"] = 0.0

    # -----------------------------------------------------------------------
    # Шаг 4: Кластеризация
    # -----------------------------------------------------------------------
    logger.info("=== Шаг 4: Кластеризация ===")
    from .clustering import SeismicClusterAnalyzer

    if use_tectonic_v2:
        from .tectonic_distance_v2 import TectonicDistanceV2
        dist_calc = TectonicDistanceV2()
        dist_calc.build_graph()
        logger.info("Используем TectonicDistanceV2")
    else:
        from .tectonic_distance import TectonicDistanceCalculator
        dist_calc = TectonicDistanceCalculator()
        dist_calc.build_graph()
        logger.info("Используем TectonicDistanceCalculator")

    analyzer = SeismicClusterAnalyzer()

    try:
        df_nn = analyzer.find_nearest_neighbor(df_analysis, dist_calculator=dist_calc)
    except Exception as exc:
        logger.warning("find_nearest_neighbor с dist_calc не удалось: %s. Используем гаверсинус.", exc)
        df_nn = analyzer.find_nearest_neighbor(df_analysis)

    series_list = analyzer.global_series(
        df_nn,
        time_window_years=time_window_years,
        min_events=min_events,
        min_magnitude=min_magnitude,
    )

    results["n_series"] = len(series_list)
    results["series"] = series_list
    logger.info("Найдено %d глобальных серий", len(series_list))

    # -----------------------------------------------------------------------
    # Шаг 5: Monte Carlo
    # -----------------------------------------------------------------------
    logger.info("=== Шаг 5: Monte Carlo (n=%d) ===", n_monte_carlo)
    try:
        from .monte_carlo import MonteCarloTester
        mc_tester = MonteCarloTester()
        p_values: dict[str, float] = {}
        for i, series in enumerate(series_list):
            series_id = f"series_{i}"
            try:
                pval = mc_tester.pvalue(series, n_simulations=min(n_monte_carlo, 1000))
                p_values[series_id] = float(pval)
            except Exception as exc:
                logger.debug("p-value для %s: ошибка %s", series_id, exc)
                p_values[series_id] = 1.0

        results["p_values"] = p_values
        logger.info("p-values вычислены для %d серий", len(p_values))
    except Exception as exc:
        logger.warning("Monte Carlo не выполнен: %s", exc)
        results["p_values"] = {}

    # -----------------------------------------------------------------------
    # Шаг 6: FDR коррекция
    # -----------------------------------------------------------------------
    if apply_fdr and results["p_values"]:
        logger.info("=== Шаг 6: FDR коррекция ===")
        from .multiple_testing import apply_bh_to_series
        fdr_table = apply_bh_to_series(results["p_values"], alpha=0.05)
        results["fdr_table"] = fdr_table
        n_sig = int(fdr_table["significant"].sum())
        logger.info("После FDR: %d значимых серий из %d", n_sig, len(fdr_table))
    else:
        logger.info("=== Шаг 6: FDR коррекция пропущена ===")
        results["fdr_table"] = None

    # -----------------------------------------------------------------------
    # Шаг 7: ETAS валидация (опционально)
    # -----------------------------------------------------------------------
    if run_etas_validation:
        logger.info("=== Шаг 7: ETAS валидация (n=%d каталогов) ===", n_etas_catalogs)
        from .etas_validation import ETASCatalogGenerator
        etas_gen = ETASCatalogGenerator(m_min=min_magnitude)
        etas_results = etas_gen.run_false_positive_analysis(
            cluster_analyzer=analyzer,
            n_catalogs=n_etas_catalogs,
            seed=42,
        )
        results["etas_validation"] = {
            "false_positive_rate": etas_results["false_positive_rate"],
            "mean_false_series": etas_results["mean_false_series"],
        }
        logger.info(
            "ETAS: FPR=%.3f, mean_false=%.2f",
            etas_results["false_positive_rate"],
            etas_results["mean_false_series"],
        )
    else:
        logger.info("=== Шаг 7: ETAS валидация пропущена ===")
        results["etas_validation"] = None

    # -----------------------------------------------------------------------
    # Шаг 8: Сохранение результатов
    # -----------------------------------------------------------------------
    logger.info("=== Шаг 8: Сохранение результатов ===")
    results["elapsed_sec"] = round(time.time() - t0, 2)
    _save_results(results, out_dir)

    logger.info(
        "Пайплайн завершён за %.1f сек. Серий: %d",
        results["elapsed_sec"], results["n_series"],
    )
    return results
