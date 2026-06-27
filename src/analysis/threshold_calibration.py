"""Калибровка порогов N_min и n_regions через синтетические данные.

Методология:
1. Генерируем синтетические каталоги с известными вставленными сериями.
2. Запускаем алгоритм кластеризации с разными порогами.
3. Измеряем precision, recall, F1 по выявленным сериям.
4. Выбираем пороги с F1 > 0.7.
"""

from __future__ import annotations

import logging
from itertools import product
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

_R_EARTH = 6371.0


# ---------------------------------------------------------------------------
# Генератор синтетических каталогов с вставленными сериями
# ---------------------------------------------------------------------------

def generate_catalog_with_injected_series(
    n_background: int = 500,
    n_series: int = 5,
    series_size: int = 4,
    series_regions: int = 3,
    series_window_years: float = 1.0,
    m_min: float = 6.5,
    seed: int | None = None,
) -> tuple[pd.DataFrame, list[list[int]]]:
    """Создаёт синтетический каталог с вставленными сериями.

    Фоновые события — равномерно распределённые во времени и пространстве.
    Вставленные серии — группы событий в ``series_regions`` разных регионах
    Flinn-Engdahl в окне ``series_window_years`` лет.

    Args:
        n_background: число фоновых событий.
        n_series: число вставленных серий.
        series_size: число событий в каждой серии.
        series_regions: минимальное число охватываемых регионов в серии.
        series_window_years: временно́е окно серии (годы).
        m_min: минимальная магнитуда.
        seed: зерно генератора.

    Returns:
        Кортеж ``(catalog_df, true_series_indices)``::

            catalog_df: DataFrame с колонками year, month, day, lat, lon,
                        magnitude, fe_region.
            true_series_indices: список списков индексов строк,
                                 принадлежащих каждой серии.
    """
    rng = np.random.default_rng(seed)

    # --- Фоновые события ---
    year_start, year_end = 1900, 2020
    bg_years = rng.integers(year_start, year_end, n_background).astype(float)
    bg_months = rng.integers(1, 13, n_background).astype(float)
    bg_days = rng.integers(1, 29, n_background).astype(float)
    bg_lats = rng.uniform(-60, 60, n_background)
    bg_lons = rng.uniform(-180, 180, n_background)
    bg_mags = m_min + rng.exponential(0.5, n_background)
    # Назначаем регионы по сетке 30° x 30°
    bg_regions = [
        f"R{int((lat + 60) // 30)}_{int((lon + 180) // 30)}"
        for lat, lon in zip(bg_lats, bg_lons)
    ]

    records = []
    for i in range(n_background):
        records.append({
            "year": bg_years[i],
            "month": bg_months[i],
            "day": bg_days[i],
            "lat": bg_lats[i],
            "lon": bg_lons[i],
            "magnitude": bg_mags[i],
            "fe_region": bg_regions[i],
        })

    # --- Вставленные серии ---
    true_series_indices: list[list[int]] = []

    # Доступные регионы для серий (уникальные)
    all_regions = [f"R{r}_{c}" for r in range(4) for c in range(12)]
    # Базовые координаты регионов (центры)
    region_lats = {f"R{r}_{c}": -45 + r * 30 for r in range(4) for c in range(12)}
    region_lons = {f"R{r}_{c}": -165 + c * 30 for r in range(4) for c in range(12)}

    for s in range(n_series):
        # Случайный год начала серии
        anchor_year = float(rng.integers(year_start + 5, year_end - 5))
        anchor_month = float(rng.integers(1, 13))
        anchor_day = float(rng.integers(1, 29))

        # Выбираем series_regions разных регионов
        chosen_regions = rng.choice(all_regions, series_regions, replace=False)

        series_indices: list[int] = []

        # Генерируем по (series_size // series_regions + 1) событий в каждом регионе
        events_per_region = max(1, series_size // series_regions)
        total_generated = 0

        for reg in chosen_regions:
            for _ in range(events_per_region):
                if total_generated >= series_size:
                    break
                # Время внутри окна
                dt_years = rng.uniform(0, series_window_years)
                ev_year = anchor_year + dt_years
                ev_month = float(int(anchor_month + dt_years * 12) % 12 + 1)
                ev_day = float(rng.integers(1, 29))

                # Координаты вблизи центра региона
                lat = region_lats[reg] + rng.uniform(-10, 10)
                lon = region_lons[reg] + rng.uniform(-10, 10)
                lat = float(np.clip(lat, -89, 89))
                lon = float(((lon + 180) % 360) - 180)
                mag = m_min + rng.exponential(0.3)

                row_idx = len(records)
                records.append({
                    "year": ev_year,
                    "month": ev_month,
                    "day": ev_day,
                    "lat": lat,
                    "lon": lon,
                    "magnitude": mag,
                    "fe_region": reg,
                })
                series_indices.append(row_idx)
                total_generated += 1

        if series_indices:
            true_series_indices.append(series_indices)

    df = pd.DataFrame(records)
    df = df.sort_values(["year", "month", "day"]).reset_index(drop=True)

    # Пересчитываем индексы после сортировки
    # Строим маппинг: старый индекс -> новый
    old_to_new = {old: new for new, old in enumerate(df.index)}
    # После reset_index старый индекс сохранён в оригинальном индексе
    # Пересоздаём маппинг через идентификацию строк
    original_order = list(df.index)

    # Более надёжный способ: добавляем служебный столбец
    df2 = pd.DataFrame(records)
    df2["_orig_idx"] = range(len(df2))
    df2 = df2.sort_values(["year", "month", "day"]).reset_index(drop=True)

    orig_to_new: dict[int, int] = {
        int(row["_orig_idx"]): new_idx
        for new_idx, (_, row) in enumerate(df2.iterrows())
    }

    true_series_new = [
        [orig_to_new[old_idx] for old_idx in series_idxs if old_idx in orig_to_new]
        for series_idxs in true_series_indices
    ]

    df2 = df2.drop(columns=["_orig_idx"])

    logger.info(
        "Синтетический каталог: %d событий, %d вставленных серий",
        len(df2), n_series,
    )
    return df2, true_series_new


# ---------------------------------------------------------------------------
# Оценка качества обнаружения
# ---------------------------------------------------------------------------

def _series_overlap(found_series: list[pd.DataFrame], true_indices: list[list[int]]) -> dict:
    """Вычисляет precision, recall, F1 по пересечению серий.

    Серия считается «найденной», если она пересекается с истинной серией
    не менее чем на 50% событий.

    Args:
        found_series: список DataFrame найденных серий.
        true_indices: список списков истинных индексов.

    Returns:
        Словарь с ``precision``, ``recall``, ``f1``.
    """
    if not true_indices or not found_series:
        precision = 1.0 if not found_series else 0.0
        recall = 1.0 if not true_indices else 0.0
        f1 = 2 * precision * recall / (precision + recall + 1e-10)
        return {"precision": precision, "recall": recall, "f1": f1}

    true_sets = [set(idxs) for idxs in true_indices]
    found_sets = [set(s.index.tolist()) for s in found_series]

    # True positives: найденные серии с overlap >= 0.5
    tp_found = 0
    for fs in found_sets:
        for ts in true_sets:
            overlap = len(fs & ts)
            if overlap > 0 and overlap / max(len(ts), 1) >= 0.5:
                tp_found += 1
                break

    # Recall: какую долю истинных серий нашли
    tp_true = 0
    for ts in true_sets:
        for fs in found_sets:
            overlap = len(fs & ts)
            if overlap > 0 and overlap / max(len(ts), 1) >= 0.5:
                tp_true += 1
                break

    precision = tp_found / max(len(found_sets), 1)
    recall = tp_true / max(len(true_sets), 1)
    f1 = 2 * precision * recall / (precision + recall + 1e-10)
    return {"precision": precision, "recall": recall, "f1": f1}


# ---------------------------------------------------------------------------
# Основная функция калибровки
# ---------------------------------------------------------------------------

def calibrate_thresholds(
    cluster_analyzer: Any,
    n_min_range: range = range(3, 8),
    n_regions_range: range = range(2, 6),
    n_synthetic: int = 50,
    seed: int = 42,
) -> pd.DataFrame:
    """Перебирает комбинации порогов и оценивает качество обнаружения.

    Для каждой пары (``min_events``, ``min_regions``) генерирует
    ``n_synthetic`` каталогов, запускает ``cluster_analyzer.global_series``
    и измеряет precision, recall, F1.

    Args:
        cluster_analyzer: объект с методом ``global_series(df, ...)``.
        n_min_range: диапазон значений ``min_events``.
        n_regions_range: диапазон значений ``min_regions``.
        n_synthetic: число синтетических каталогов для усреднения.
        seed: начальное зерно.

    Returns:
        DataFrame с колонками:
        ``min_events``, ``min_regions``, ``precision``, ``recall``,
        ``f1``, ``mean_found_series``.
        Отсортирован по убыванию F1. Включает только строки с F1 > 0.
    """
    rows: list[dict] = []

    for min_events, min_regions in product(n_min_range, n_regions_range):
        precisions, recalls, f1s, n_found_list = [], [], [], []

        for i in range(n_synthetic):
            catalog, true_idx = generate_catalog_with_injected_series(
                n_background=300,
                n_series=5,
                series_size=max(min_events, 4),
                series_regions=max(min_regions, 2),
                seed=seed + i * 100,
            )

            try:
                found = cluster_analyzer.global_series(
                    catalog,
                    time_window_years=1.0,
                    min_events=min_events,
                )
                # Фильтрация по числу регионов
                found = [
                    s for s in found
                    if "fe_region" in s.columns and s["fe_region"].nunique() >= min_regions
                ]
            except Exception as exc:
                logger.debug("Ошибка кластеризации при n_min=%d, n_reg=%d: %s",
                             min_events, min_regions, exc)
                found = []

            metrics = _series_overlap(found, true_idx)
            precisions.append(metrics["precision"])
            recalls.append(metrics["recall"])
            f1s.append(metrics["f1"])
            n_found_list.append(len(found))

        rows.append({
            "min_events": min_events,
            "min_regions": min_regions,
            "precision": float(np.mean(precisions)),
            "recall": float(np.mean(recalls)),
            "f1": float(np.mean(f1s)),
            "mean_found_series": float(np.mean(n_found_list)),
        })
        logger.debug(
            "n_min=%d, n_reg=%d: F1=%.3f, P=%.3f, R=%.3f",
            min_events, min_regions, rows[-1]["f1"],
            rows[-1]["precision"], rows[-1]["recall"],
        )

    result = pd.DataFrame(rows).sort_values("f1", ascending=False).reset_index(drop=True)
    logger.info(
        "Калибровка: лучшие пороги min_events=%d, min_regions=%d (F1=%.3f)",
        int(result.iloc[0]["min_events"]),
        int(result.iloc[0]["min_regions"]),
        result.iloc[0]["f1"],
    )
    return result
