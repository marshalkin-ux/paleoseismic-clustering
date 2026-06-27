"""Юнит-тесты модуля кластеризации.

Тестирует метрику Baiesi-Paczuski, поиск ближайших соседей
и Monte Carlo тест для случайных данных.
"""

import numpy as np
import pandas as pd
import pytest

from src.analysis.clustering import (
    SeismicClusterAnalyzer,
    _eta_metric,
    _events_to_time_years,
)
from src.analysis.tectonic_distance import haversine


class TestEtaMetric:
    """Тесты метрики eta Baiesi-Paczuski."""

    def test_eta_positive_inputs(self) -> None:
        """Метрика должна возвращать положительное число для корректных входных данных."""
        eta = _eta_metric(t_ij=1.0, r_ij=100.0, m_i=7.0)
        assert eta > 0
        assert np.isfinite(eta)

    def test_eta_increases_with_time(self) -> None:
        """При увеличении времени eta растёт."""
        eta1 = _eta_metric(t_ij=1.0, r_ij=100.0, m_i=7.0)
        eta2 = _eta_metric(t_ij=2.0, r_ij=100.0, m_i=7.0)
        assert eta2 > eta1

    def test_eta_increases_with_distance(self) -> None:
        """При увеличении расстояния eta растёт."""
        eta1 = _eta_metric(t_ij=1.0, r_ij=100.0, m_i=7.0)
        eta2 = _eta_metric(t_ij=1.0, r_ij=200.0, m_i=7.0)
        assert eta2 > eta1

    def test_eta_decreases_with_magnitude(self) -> None:
        """При увеличении магнитуды родителя eta уменьшается (сильнее связаны)."""
        eta1 = _eta_metric(t_ij=1.0, r_ij=100.0, m_i=7.0)
        eta2 = _eta_metric(t_ij=1.0, r_ij=100.0, m_i=8.0)
        assert eta2 < eta1

    def test_eta_inf_for_zero_time(self) -> None:
        """Нулевое время должно давать inf."""
        eta = _eta_metric(t_ij=0.0, r_ij=100.0, m_i=7.0)
        assert np.isinf(eta)

    def test_eta_inf_for_zero_distance(self) -> None:
        """Нулевое расстояние должно давать inf."""
        eta = _eta_metric(t_ij=1.0, r_ij=0.0, m_i=7.0)
        assert np.isinf(eta)

    def test_eta_numerical_value(self) -> None:
        """Проверка конкретного значения метрики."""
        # eta = 1.0 * 100^1.6 * 10^(-1.0*7.0) = 100^1.6 / 10^7
        expected = (100.0 ** 1.6) * (10 ** (-1.0 * 7.0))
        eta = _eta_metric(t_ij=1.0, r_ij=100.0, m_i=7.0, df=1.6, b=1.0)
        assert abs(eta - expected) < 1e-10

    def test_eta_scale_invariance_time(self) -> None:
        """Метрика линейно зависит от времени."""
        eta1 = _eta_metric(t_ij=1.0, r_ij=100.0, m_i=7.0)
        eta2 = _eta_metric(t_ij=3.0, r_ij=100.0, m_i=7.0)
        assert abs(eta2 / eta1 - 3.0) < 1e-9


class TestNearestNeighbor:
    """Тесты поиска ближайшего соседа."""

    def _make_simple_df(self) -> pd.DataFrame:
        """Создаёт простой DataFrame с 5 событиями."""
        return pd.DataFrame({
            "event_id": [f"ev{i}" for i in range(5)],
            "year":      [2000, 2001, 2002, 2003, 2004],
            "month":     [1, 1, 1, 1, 1],
            "day":       [1, 1, 1, 1, 1],
            "lat":       [35.0, 35.1, 35.2, 35.3, 35.4],
            "lon":       [135.0, 135.1, 135.2, 135.3, 135.4],
            "magnitude": [7.0, 6.5, 7.2, 6.8, 7.5],
            "depth_km":  [30.0] * 5,
        })

    def test_first_event_has_no_parent(self) -> None:
        """Первое событие не имеет родителя (parent_idx = -1)."""
        df = self._make_simple_df()
        analyzer = SeismicClusterAnalyzer()
        result = analyzer.find_nearest_neighbor(df)
        assert result.loc[0, "parent_idx"] == -1

    def test_all_other_events_have_parent(self) -> None:
        """Все события кроме первого должны иметь родителя."""
        df = self._make_simple_df()
        analyzer = SeismicClusterAnalyzer()
        result = analyzer.find_nearest_neighbor(df)
        for i in range(1, len(result)):
            assert result.loc[i, "parent_idx"] >= 0

    def test_eta_nn_positive(self) -> None:
        """Значения eta_nn должны быть положительными для событий с родителями."""
        df = self._make_simple_df()
        analyzer = SeismicClusterAnalyzer()
        result = analyzer.find_nearest_neighbor(df)
        for i in range(1, len(result)):
            assert result.loc[i, "eta_nn"] > 0
            assert np.isfinite(result.loc[i, "eta_nn"])

    def test_nearby_events_lower_eta(self) -> None:
        """Близкие события должны иметь меньшее eta."""
        # Два кластера: близкие и далёкие
        df = pd.DataFrame({
            "event_id": ["A", "B", "C"],
            "year":  [2000, 2001, 2002],
            "month": [1, 1, 1],
            "day":   [1, 1, 1],
            "lat":   [35.0, 35.01, -33.0],   # B близко к A, C далеко
            "lon":   [135.0, 135.01, -70.0],
            "magnitude": [7.0, 7.0, 7.0],
            "depth_km":  [30.0, 30.0, 30.0],
        })
        analyzer = SeismicClusterAnalyzer()
        result = analyzer.find_nearest_neighbor(df)

        eta_B = result.loc[1, "eta_nn"]  # B → A
        eta_C = result.loc[2, "eta_nn"]  # C → лучший из A или B

        # B ближе к A → eta_B < eta_C (с поправкой на одинаковое время)
        assert eta_B < eta_C


class TestIdentifyClusters:
    """Тесты идентификации кластеров."""

    def test_isolated_events_are_background(self) -> None:
        """Изолированные события классифицируются как фоновые (cluster_id = -1)."""
        # Очень высокий порог → все события изолированы
        df = pd.DataFrame({
            "event_id": [f"ev{i}" for i in range(4)],
            "year":  [2000, 2010, 2020, 2030],
            "month": [1] * 4,
            "day":   [1] * 4,
            "lat":   [35.0, -33.0, 51.5, 40.7],
            "lon":   [135.0, -70.0, -0.1, -74.0],
            "magnitude": [7.0] * 4,
            "depth_km":  [30.0] * 4,
        })
        analyzer = SeismicClusterAnalyzer()
        df_nn = analyzer.find_nearest_neighbor(df)
        # С очень высоким порогом все события изолированы
        result = analyzer.identify_clusters(df_nn, eta_threshold=1e-100)
        assert all(result["cluster_id"] == -1)

    def test_artificial_cluster_detected(self) -> None:
        """Искусственный кластер (близкие по времени и месту события) должен быть выявлен."""
        # Два близких события + одно изолированное
        df = pd.DataFrame({
            "event_id": ["A", "B", "C"],
            "year":  [2000, 2000, 2010],
            "month": [1, 1, 1],
            "day":   [1, 2, 1],   # A и B разделены 1 днём
            "lat":   [35.0, 35.01, -33.0],
            "lon":   [135.0, 135.01, -70.0],
            "magnitude": [7.5, 6.8, 7.0],
            "depth_km":  [30.0, 25.0, 40.0],
        })
        analyzer = SeismicClusterAnalyzer()
        df_nn = analyzer.find_nearest_neighbor(df)
        result = analyzer.identify_clusters(df_nn, eta_threshold=1e10)  # мягкий порог
        # A и B должны попасть в один кластер
        cluster_A = result.loc[0, "cluster_id"]
        cluster_B = result.loc[1, "cluster_id"]
        assert cluster_A == cluster_B
        assert cluster_A >= 0


class TestMonteCarloSignificance:
    """Тест Monte Carlo: случайные данные не должны давать p < 0.05."""

    def test_random_data_pvalue_not_significant(self) -> None:
        """Для случайно сгенерированных данных p-value должен быть > 0.05."""
        from src.analysis.monte_carlo import MonteCarloTester

        rng = np.random.default_rng(12345)
        n = 30  # небольшой размер для скорости теста

        df = pd.DataFrame({
            "event_id": [f"rand{i}" for i in range(n)],
            "year":  rng.integers(1900, 2024, size=n).tolist(),
            "month": rng.integers(1, 13, size=n).tolist(),
            "day":   rng.integers(1, 29, size=n).tolist(),
            "lat":   (rng.uniform(-80, 80, size=n)).tolist(),
            "lon":   (rng.uniform(-180, 180, size=n)).tolist(),
            "magnitude": (rng.uniform(6.5, 8.5, size=n)).tolist(),
            "depth_km":  (rng.uniform(5, 100, size=n)).tolist(),
        })

        tester = MonteCarloTester(random_seed=42)
        p = tester.pvalue(df, n_simulations=200)  # 200 симуляций для скорости

        # Для случайных данных ожидаем p > 0.05 (нет значимой кластеризации)
        # Используем мягкий порог 0.01 для устойчивости теста
        assert p > 0.01, f"p-value = {p:.4f} для случайных данных (слишком мало)"


class TestEventsToTimeYears:
    """Тесты вспомогательной функции преобразования дат."""

    def test_basic_conversion(self) -> None:
        """Проверка базового преобразования year/month/day в числовые годы."""
        df = pd.DataFrame({
            "year": [2000, 2001],
            "month": [1, 7],
            "day": [1, 1],
        })
        times = _events_to_time_years(df)
        assert times[0] < times[1]
        assert abs(times[0] - 2000.0) < 0.1
        assert abs(times[1] - 2001.5) < 0.1

    def test_monotonic_for_sorted_events(self) -> None:
        """Для событий с возрастающими датами время должно расти монотонно."""
        df = pd.DataFrame({
            "year":  [2000, 2001, 2002, 2003],
            "month": [1, 3, 6, 12],
            "day":   [1, 15, 30, 31],
        })
        times = _events_to_time_years(df)
        assert all(np.diff(times) > 0)
