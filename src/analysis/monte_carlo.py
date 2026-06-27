"""Monte Carlo тестирование значимости кластеризации.

Проверяет, превышает ли наблюдаемая кластеризация случайный уровень
путём перемешивания временны́х меток при фиксированных координатах.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _mean_log_eta(df: pd.DataFrame, b: float = 1.0, df_param: float = 1.6) -> float:
    """Вычисляет среднее log10(eta) ближайшего соседа как статистику кластеризации.

    Чем меньше значение, тем сильнее кластеризация.
    """
    from .clustering import _events_to_time_years, _eta_metric
    from .tectonic_distance import haversine

    df = df.copy().sort_values(["year", "month", "day"]).reset_index(drop=True)
    times = _events_to_time_years(df)
    lat_col = "latitude" if "latitude" in df.columns else "lat"
    lon_col = "longitude" if "longitude" in df.columns else "lon"
    lats = df[lat_col].fillna(0).values
    lons = df[lon_col].fillna(0).values
    mags = df["magnitude"].fillna(6.5).values

    log_etas = []
    for j in range(1, len(df)):
        best_eta = np.inf
        for i in range(j):
            t_ij = times[j] - times[i]
            if t_ij <= 0:
                continue
            r_ij = haversine(lats[i], lons[i], lats[j], lons[j]) * 1.5
            eta = _eta_metric(t_ij, r_ij, mags[i], df_param, b)
            if eta < best_eta:
                best_eta = eta
        if np.isfinite(best_eta) and best_eta > 0:
            log_etas.append(np.log10(best_eta))

    return float(np.mean(log_etas)) if log_etas else 0.0


class MonteCarloTester:
    """Тестирует значимость кластеризации методом Monte Carlo.

    Пример::

        tester = MonteCarloTester()
        p = tester.pvalue(observed_df, n_simulations=1000)
        ci = tester.bootstrap_series(series_df, n=500)
    """

    def __init__(self, analyzer=None, random_seed: int = 42) -> None:
        self.analyzer = analyzer
        self.rng = np.random.default_rng(random_seed)

    def shuffle_times(
        self,
        df: pd.DataFrame,
        n_simulations: int = 10000,
    ) -> list[pd.DataFrame]:
        """Генерирует n_simulations суррогатных каталогов.

        Перемешивает временны́е метки (year, month, day),
        сохраняя координаты и магнитуды.

        Args:
            df: исходный DataFrame.
            n_simulations: количество суррогатов.

        Returns:
            Список суррогатных DataFrame.
        """
        logger.info("Генерация %d суррогатных каталогов...", n_simulations)
        time_cols = ["year", "month", "day"]
        available = [c for c in time_cols if c in df.columns]

        time_data = df[available].values.copy()
        surrogates = []

        for _ in range(n_simulations):
            perm = self.rng.permutation(len(time_data))
            shuffled = df.copy()
            shuffled[available] = time_data[perm]
            surrogates.append(shuffled)

        return surrogates

    def compute_cluster_statistic(self, df: pd.DataFrame) -> float:
        """Статистика кластеризации: среднее log10(eta) ближайшего соседа.

        Поддерживает оба формата: старый (year/month/day/lat/lon)
        и новый (time/latitude/longitude).

        Args:
            df: DataFrame с событиями и колонкой eta (если есть) или без неё.

        Returns:
            Скалярная статистика (чем меньше, тем сильнее кластеризация).
        """
        if "eta" in df.columns:
            etas = df["eta"].dropna()
            etas = etas[etas > 0]
            if etas.empty:
                return float("nan")
            return float(np.mean(np.log10(etas)))
        return _mean_log_eta(df)

    def run_permutation_test(
        self,
        df: pd.DataFrame,
        dist_calculator=None,
        n_simulations: int = 1000,
    ) -> dict[str, Any]:
        """Пермутационный тест значимости кластеризации.

        Нулевая гипотеза: нет временно-пространственной кластеризации.
        При каждой перестановке временны́х меток вычисляется статистика
        среднего log10(eta), строится эмпирическое распределение.

        Args:
            df: каталог с колонками time, latitude, longitude, magnitude.
            dist_calculator: TectonicDistanceCalculator (опционально).
            n_simulations: число перестановок.

        Returns:
            Словарь с ключами observed, simulated, pvalue, zscore.
        """
        from .clustering import SeismicClusterAnalyzer

        analyzer = self.analyzer or SeismicClusterAnalyzer()

        obs_df = analyzer.find_nearest_neighbor(df, dist_calculator=dist_calculator)
        observed = self.compute_cluster_statistic(obs_df)

        times_array = df["time"].values.copy()
        simulated_stats = np.empty(n_simulations)

        for sim in range(n_simulations):
            perm_df = df.copy()
            perm_times = times_array.copy()
            self.rng.shuffle(perm_times)
            perm_df["time"] = perm_times

            try:
                perm_nn = analyzer.find_nearest_neighbor(
                    perm_df, dist_calculator=dist_calculator
                )
                simulated_stats[sim] = self.compute_cluster_statistic(perm_nn)
            except Exception:
                simulated_stats[sim] = float("nan")

        valid_sim = simulated_stats[~np.isnan(simulated_stats)]
        if len(valid_sim) == 0:
            return {
                "observed": observed,
                "simulated": simulated_stats,
                "pvalue": float("nan"),
                "zscore": float("nan"),
            }

        pvalue = float(np.mean(valid_sim <= observed))
        sim_mean = float(np.mean(valid_sim))
        sim_std = float(np.std(valid_sim, ddof=1))
        zscore = (observed - sim_mean) / max(sim_std, 1e-30)

        return {
            "observed": observed,
            "simulated": simulated_stats,
            "pvalue": pvalue,
            "zscore": float(zscore),
        }

    def pvalue(
        self,
        observed_df: pd.DataFrame,
        n_simulations: int = 10000,
    ) -> float:
        """Вычисляет p-value для наблюдаемой кластеризации.

        H0: временны́е метки независимы от координат (нет кластеризации).

        Args:
            observed_df: наблюдаемый каталог.
            n_simulations: число суррогатных каталогов.

        Returns:
            p-value (< 0.05 → значимая кластеризация).
        """
        obs_stat = self.compute_cluster_statistic(observed_df)
        logger.info("Наблюдаемая статистика: %.4f", obs_stat)

        surrogates = self.shuffle_times(observed_df, n_simulations)
        surrogate_stats = []

        for k, surr in enumerate(surrogates):
            stat = self.compute_cluster_statistic(surr)
            surrogate_stats.append(stat)
            if (k + 1) % 1000 == 0:
                logger.debug("Суррогат %d/%d", k + 1, n_simulations)

        surrogate_array = np.array(surrogate_stats)

        # p-value = доля суррогатов с более сильной кластеризацией (меньшим eta)
        p = float(np.mean(surrogate_array <= obs_stat))
        logger.info("p-value = %.4f (n_sim=%d)", p, n_simulations)
        return p

    def bootstrap_series(
        self,
        observed_series: pd.DataFrame,
        n: int = 1000,
    ) -> dict[str, tuple[float, float]]:
        """Доверительные интервалы для характеристик серии методом bootstrap.

        Args:
            observed_series: DataFrame одной серии (все события серии).
            n: количество bootstrap-выборок.

        Returns:
            Словарь {характеристика: (lower_95, upper_95)}.
        """
        from .statistics import (
            interevent_distribution,
            magnitude_energy_release,
            spatial_extent,
        )

        m = len(observed_series)
        if m < 3:
            logger.warning("Слишком мало событий для bootstrap (%d)", m)
            return {}

        results: dict[str, list[float]] = {
            "duration_years": [],
            "spatial_extent_deg2": [],
            "n_regions": [],
            "total_moment": [],
        }

        for _ in range(n):
            sample = observed_series.sample(m, replace=True)
            years = sample["year"].dropna().values
            if len(years) > 1:
                results["duration_years"].append(float(np.ptp(years)))

            if "fe_region" in sample.columns:
                results["n_regions"].append(float(sample["fe_region"].nunique()))

            extent = spatial_extent(sample)
            results["spatial_extent_deg2"].append(extent)

            moment = magnitude_energy_release(sample)
            results["total_moment"].append(moment)

        ci: dict[str, tuple[float, float]] = {}
        for key, vals in results.items():
            if vals:
                arr = np.array(vals)
                ci[key] = (
                    float(np.percentile(arr, 2.5)),
                    float(np.percentile(arr, 97.5)),
                )

        return ci
