"""Юнит-тесты статистических функций.

Тестирует оценку магнитуды полноты Mc и анализ распределения интервалов.
"""

import numpy as np
import pandas as pd
import pytest

from src.analysis.completeness import CompletenessAnalyzer
from src.analysis.statistics import (
    interevent_distribution,
    magnitude_energy_release,
    series_summary_table,
    spatial_extent,
)


def _synthetic_catalog(
    n_events: int = 200,
    mc_true: float = 5.5,
    b_true: float = 1.0,
    seed: int = 42,
) -> pd.DataFrame:
    """Генерирует синтетический каталог по закону Gutenberg-Richter."""
    rng = np.random.default_rng(seed)

    # Магнитуды по степенному закону (экспоненциальное распределение)
    mags = mc_true - np.log10(rng.uniform(0, 1, size=n_events * 3)) / b_true
    mags = mags[mags >= mc_true][:n_events]
    mags = np.clip(mags, mc_true, mc_true + 4.0)

    n = len(mags)
    years = rng.integers(1990, 2024, size=n)
    months = rng.integers(1, 13, size=n)
    days = rng.integers(1, 29, size=n)
    lats = rng.uniform(-60, 60, size=n)
    lons = rng.uniform(-180, 180, size=n)

    return pd.DataFrame({
        "event_id": [f"synth{i}" for i in range(n)],
        "year": years,
        "month": months,
        "day": days,
        "lat": lats,
        "lon": lons,
        "magnitude": mags,
        "magnitude_error": [0.1] * n,
        "depth_km": rng.uniform(5, 100, size=n),
        "region": ["Test Region"] * n,
        "fe_region": [1] * n,
        "quality_score": [0.9] * n,
    })


class TestEstimateMc:
    """Тесты оценки магнитуды полноты Mc."""

    def test_mc_close_to_true_value(self) -> None:
        """Mc должна быть вблизи истинного значения для синтетического каталога."""
        mc_true = 5.5
        df = _synthetic_catalog(n_events=300, mc_true=mc_true, seed=0)
        analyzer = CompletenessAnalyzer()
        mc_est = analyzer.estimate_mc(df)
        # Допуск ±0.5 магнитудной единицы
        assert abs(mc_est - mc_true) <= 0.5, (
            f"Mc оценена как {mc_est:.2f}, истинное = {mc_true:.2f}"
        )

    def test_mc_below_max_magnitude(self) -> None:
        """Mc не может быть выше максимальной магнитуды в каталоге."""
        df = _synthetic_catalog(n_events=100, mc_true=6.0)
        analyzer = CompletenessAnalyzer()
        mc = analyzer.estimate_mc(df)
        assert mc <= df["magnitude"].max()

    def test_mc_above_min_magnitude(self) -> None:
        """Mc не может быть ниже минимальной магнитуды в каталоге."""
        df = _synthetic_catalog(n_events=100, mc_true=5.0)
        analyzer = CompletenessAnalyzer()
        mc = analyzer.estimate_mc(df)
        assert mc >= df["magnitude"].min()

    def test_mc_with_few_events(self) -> None:
        """При малом числе событий функция должна работать без исключений."""
        df = _synthetic_catalog(n_events=5, mc_true=6.0)
        analyzer = CompletenessAnalyzer()
        mc = analyzer.estimate_mc(df)
        assert np.isfinite(mc)

    def test_bvalue_positive(self) -> None:
        """b-value должно быть положительным."""
        df = _synthetic_catalog(n_events=200, mc_true=5.5, b_true=1.0)
        analyzer = CompletenessAnalyzer()
        mc = analyzer.estimate_mc(df)
        b, sigma = analyzer.compute_bvalue(df, mc)
        assert b > 0
        assert sigma > 0

    def test_bvalue_close_to_true(self) -> None:
        """b-value должно быть вблизи истинного значения 1.0."""
        df = _synthetic_catalog(n_events=500, mc_true=5.0, b_true=1.0, seed=7)
        analyzer = CompletenessAnalyzer()
        mc = analyzer.estimate_mc(df)
        b, sigma = analyzer.compute_bvalue(df, mc)
        # Допуск 0.3
        assert abs(b - 1.0) <= 0.3, f"b = {b:.3f}, ожидается ~1.0"


class TestInterventDistribution:
    """Тесты распределения интервалов."""

    def _make_series(self, n: int = 10, seed: int = 42) -> pd.DataFrame:
        """Создаёт простую серию с временны́ми метками."""
        rng = np.random.default_rng(seed)
        years = sorted(rng.integers(1900, 2000, size=n))
        return pd.DataFrame({
            "year": years,
            "month": rng.integers(1, 13, size=n),
            "day": rng.integers(1, 29, size=n),
            "lat": rng.uniform(-60, 60, size=n),
            "lon": rng.uniform(-180, 180, size=n),
            "magnitude": rng.uniform(6.5, 8.0, size=n),
        })

    def test_returns_dict_with_intervals(self) -> None:
        """Функция должна возвращать словарь с ключом intervals_days."""
        series = self._make_series()
        result = interevent_distribution(series)
        assert "intervals_days" in result
        assert len(result["intervals_days"]) == len(series) - 1

    def test_intervals_positive(self) -> None:
        """Все интервалы должны быть неотрицательными."""
        series = self._make_series(n=15)
        result = interevent_distribution(series)
        assert all(result["intervals_days"] >= 0)

    def test_single_event_returns_empty(self) -> None:
        """Одиночное событие должно возвращать пустые интервалы."""
        series = pd.DataFrame({
            "year": [2000], "month": [1], "day": [1],
            "lat": [35.0], "lon": [135.0], "magnitude": [7.0],
        })
        result = interevent_distribution(series)
        assert len(result["intervals_days"]) == 0

    def test_lognorm_fit_available(self) -> None:
        """Для достаточно длинной серии должна быть доступна логнормальная аппроксимация."""
        series = self._make_series(n=20, seed=100)
        result = interevent_distribution(series)
        # Аппроксимация может не найтись при коллинеарности, но не должна выдать исключение
        assert "lognorm" in result


class TestSpatialExtent:
    """Тесты пространственного охвата серии."""

    def test_collinear_points_return_zero(self) -> None:
        """Коллинеарные точки дают нулевую площадь или маленькое значение."""
        df = pd.DataFrame({
            "lat": [35.0, 36.0, 37.0],
            "lon": [135.0, 135.0, 135.0],
        })
        extent = spatial_extent(df)
        # Коллинеарные точки → нулевая площадь
        assert extent == pytest.approx(0.0, abs=1e-6)

    def test_spread_out_events(self) -> None:
        """Широко разбросанные события дают большую площадь."""
        df_spread = pd.DataFrame({
            "lat": [-60.0, 60.0, 60.0, -60.0],
            "lon": [-120.0, -120.0, 120.0, 120.0],
        })
        df_tight = pd.DataFrame({
            "lat": [35.0, 35.1, 35.1, 35.0],
            "lon": [135.0, 135.0, 135.1, 135.1],
        })
        ext_spread = spatial_extent(df_spread)
        ext_tight = spatial_extent(df_tight)
        assert ext_spread > ext_tight

    def test_two_points_return_zero(self) -> None:
        """Два события → нулевая площадь (нет выпуклой оболочки)."""
        df = pd.DataFrame({
            "lat": [35.0, 36.0],
            "lon": [135.0, 136.0],
        })
        extent = spatial_extent(df)
        assert extent == pytest.approx(0.0, abs=1e-6)


class TestMagnitudeEnergyRelease:
    """Тесты вычисления суммарного сейсмического момента."""

    def test_empty_dataframe(self) -> None:
        """Пустой DataFrame должен давать нулевой момент."""
        df = pd.DataFrame({"magnitude": []})
        assert magnitude_energy_release(df) == 0.0

    def test_moment_increases_with_magnitude(self) -> None:
        """Большая магнитуда → больший момент."""
        df_low = pd.DataFrame({"magnitude": [6.5]})
        df_high = pd.DataFrame({"magnitude": [8.0]})
        assert magnitude_energy_release(df_high) > magnitude_energy_release(df_low)

    def test_moment_positive(self) -> None:
        """Момент всегда положительный."""
        df = pd.DataFrame({"magnitude": [7.0, 7.5, 8.0]})
        assert magnitude_energy_release(df) > 0

    def test_sum_of_moments(self) -> None:
        """Суммарный момент равен сумме индивидуальных моментов."""
        mags = [7.0, 7.5, 8.0]
        expected = sum(10 ** (1.5 * m + 9.1) for m in mags)
        df = pd.DataFrame({"magnitude": mags})
        result = magnitude_energy_release(df)
        assert abs(result - expected) / expected < 1e-6


class TestSeriesSummaryTable:
    """Тесты сводной таблицы серий."""

    def _make_series_list(self) -> list:
        """Создаёт список из 3 синтетических серий."""
        rng = np.random.default_rng(99)
        series_list = []
        for i in range(3):
            n = 5 + i * 3
            series_list.append(pd.DataFrame({
                "year":  sorted(rng.integers(1980 + i * 10, 1990 + i * 10, size=n)),
                "month": rng.integers(1, 13, size=n),
                "day":   rng.integers(1, 29, size=n),
                "lat":   rng.uniform(-60, 60, size=n),
                "lon":   rng.uniform(-180, 180, size=n),
                "magnitude": rng.uniform(6.5, 8.5, size=n),
                "fe_region": rng.integers(1, 50, size=n),
            }))
        return series_list

    def test_returns_dataframe(self) -> None:
        """Функция должна возвращать DataFrame."""
        series_list = self._make_series_list()
        table = series_summary_table(series_list)
        assert isinstance(table, pd.DataFrame)

    def test_correct_number_of_rows(self) -> None:
        """Число строк должно равняться числу серий."""
        series_list = self._make_series_list()
        table = series_summary_table(series_list)
        assert len(table) == len(series_list)

    def test_required_columns_present(self) -> None:
        """Таблица должна содержать обязательные колонки."""
        required = ["series_id", "n_events", "year_start", "year_end", "max_magnitude"]
        series_list = self._make_series_list()
        table = series_summary_table(series_list)
        for col in required:
            assert col in table.columns, f"Колонка '{col}' отсутствует"
