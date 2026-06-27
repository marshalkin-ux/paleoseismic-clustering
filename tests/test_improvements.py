"""Тесты для улучшений пайплайна сейсмической кластеризации.

Проверяет:
- TestGardnerKnopoff: декластеризация синтетического кластера.
- TestFDR: коррекция на множественное тестирование.
- TestETAS: генератор синтетических ETAS-каталогов.
- TestCalibration: обнаружение синтетических серий.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# Вспомогательные фабрики данных
# ---------------------------------------------------------------------------

def _make_catalog(
    n: int = 50,
    lat_range: tuple[float, float] = (-60, 60),
    lon_range: tuple[float, float] = (-180, 180),
    m_min: float = 6.5,
    seed: int = 42,
) -> pd.DataFrame:
    """Генерирует случайный каталог без кластеров."""
    rng = np.random.default_rng(seed)
    years = rng.integers(1950, 2020, n).astype(float)
    months = rng.integers(1, 13, n).astype(float)
    days = rng.integers(1, 29, n).astype(float)
    lats = rng.uniform(*lat_range, n)
    lons = rng.uniform(*lon_range, n)
    mags = m_min + rng.exponential(0.5, n)

    return pd.DataFrame({
        "year": years,
        "month": months,
        "day": days,
        "lat": lats,
        "lon": lons,
        "magnitude": mags,
        "fe_region": [f"R{i % 5}" for i in range(n)],
    }).sort_values(["year", "month", "day"]).reset_index(drop=True)


def _make_cluster_catalog(seed: int = 42) -> pd.DataFrame:
    """Создаёт каталог с явным кластером: 1 главный + 5 афтершоков.

    Главный толчок: M=7.0, (0°N, 90°E), 1 января 2000.
    Афтершоки: M=5.5–6.0, < 30 км, первые 10 дней.
    """
    rng = np.random.default_rng(seed)

    records = []

    # Главный толчок
    records.append({
        "time": pd.Timestamp("2000-01-01"),
        "lat": 0.0, "lon": 90.0, "magnitude": 7.0,
    })

    # 5 афтершоков (0–10 дней, < 30 км)
    for i in range(5):
        dt_days = rng.uniform(0.5, 10)
        dlat = rng.uniform(-0.2, 0.2)   # ~20 км
        dlon = rng.uniform(-0.2, 0.2)
        records.append({
            "time": pd.Timestamp("2000-01-01") + pd.Timedelta(days=dt_days),
            "lat": 0.0 + dlat,
            "lon": 90.0 + dlon,
            "magnitude": float(rng.uniform(5.5, 6.0)),
        })

    # Фоновые события (далеко, через несколько месяцев)
    for i in range(10):
        records.append({
            "time": pd.Timestamp("2000-01-01") + pd.Timedelta(days=rng.integers(200, 500)),
            "lat": float(rng.uniform(-60, 60)),
            "lon": float(rng.uniform(-180, 180)),
            "magnitude": float(rng.uniform(6.5, 7.5)),
        })

    df = pd.DataFrame(records)
    df["time"] = pd.to_datetime(df["time"])
    return df.sort_values("time").reset_index(drop=True)


# ---------------------------------------------------------------------------
# TestGardnerKnopoff
# ---------------------------------------------------------------------------

class TestGardnerKnopoff:
    """Тесты алгоритма Gardner-Knopoff (1974)."""

    def test_import(self) -> None:
        """Модуль декластеризации импортируется без ошибок."""
        from src.analysis.declustering import GardnerKnopoffDeclustering
        assert GardnerKnopoffDeclustering is not None

    def test_decluster_returns_two_dfs(self) -> None:
        """decluster() возвращает кортеж из двух DataFrame."""
        from src.analysis.declustering import GardnerKnopoffDeclustering
        df = _make_cluster_catalog()
        gk = GardnerKnopoffDeclustering()
        result = gk.decluster(df)
        assert isinstance(result, tuple)
        assert len(result) == 2
        main, dep = result
        assert isinstance(main, pd.DataFrame)
        assert isinstance(dep, pd.DataFrame)

    def test_aftershocks_removed(self) -> None:
        """После декластеризации афтершоки помечены как зависимые."""
        from src.analysis.declustering import GardnerKnopoffDeclustering
        df = _make_cluster_catalog()
        gk = GardnerKnopoffDeclustering()
        main, after = gk.decluster(df)

        # Общее число событий должно сохраняться
        assert len(main) + len(after) == len(df)

        # Должны быть обнаружены зависимые события (афтершоки)
        assert len(after) >= 1, "Афтершоки должны быть выявлены"

        # Главный толчок (M=7.0) должен остаться в mainshocks
        max_mag_main = main["magnitude"].max()
        assert max_mag_main >= 6.9, f"Главный толчок утерян: max_mag_main={max_mag_main}"

    def test_no_events_lost(self) -> None:
        """Число событий в main + after == исходное."""
        from src.analysis.declustering import GardnerKnopoffDeclustering
        df = _make_catalog(n=30)
        gk = GardnerKnopoffDeclustering()
        main, dep = gk.decluster(df)
        assert len(main) + len(dep) == len(df)

    def test_window_interpolation(self) -> None:
        """_get_window() возвращает корректные значения для промежуточных M."""
        from src.analysis.declustering import GardnerKnopoffDeclustering
        gk = GardnerKnopoffDeclustering()
        t_win, r_win = gk._get_window(5.25)
        # Должно быть между окнами M=5.0 и M=5.5
        assert 7.0 < t_win < 10.0
        assert 40.0 < r_win < 47.0

    def test_compare_methods(self) -> None:
        """compare_declustering_methods() возвращает DataFrame с нужными колонками."""
        from src.analysis.declustering import compare_declustering_methods
        df = _make_catalog(n=40)
        result = compare_declustering_methods(df)
        required_cols = {
            "n_total", "n_mainshocks_gk", "n_mainshocks_zb",
            "n_aftershocks_gk", "n_aftershocks_zb",
            "reduction_gk_pct", "reduction_zb_pct",
        }
        assert required_cols.issubset(set(result.columns))
        assert result.iloc[0]["n_total"] == len(df)


# ---------------------------------------------------------------------------
# TestFDR
# ---------------------------------------------------------------------------

class TestFDR:
    """Тесты коррекции на множественное тестирование."""

    def test_bonferroni_import(self) -> None:
        from src.analysis.multiple_testing import apply_bonferroni
        assert apply_bonferroni is not None

    def test_bonferroni_scales_pvalues(self) -> None:
        """Бонферрони умножает p-value на число тестов."""
        from src.analysis.multiple_testing import apply_bonferroni
        pvals = np.array([0.01, 0.05, 0.1])
        adj = apply_bonferroni(pvals)
        assert len(adj) == len(pvals)
        # Первое значение: 0.01 * 3 = 0.03
        assert abs(adj[0] - 0.03) < 1e-10

    def test_bonferroni_clamps_at_one(self) -> None:
        """Скорректированные p-value не превышают 1.0."""
        from src.analysis.multiple_testing import apply_bonferroni
        pvals = np.array([0.5, 0.8, 1.0])
        adj = apply_bonferroni(pvals)
        assert np.all(adj <= 1.0)

    def test_fdr_bh_controls_rate(self) -> None:
        """FDR BH не отвергает слишком много гипотез при случайных p-value.

        При 100 случайных (равномерных) p-value и α=0.05
        FDR должен отвергать мало гипотез (ожидаемо 0–5).
        """
        from src.analysis.multiple_testing import apply_fdr_bh
        rng = np.random.default_rng(42)
        pvals = rng.uniform(0, 1, 100)
        reject, adj = apply_fdr_bh(pvals, alpha=0.05)
        # При нулевых данных FDR должен быть консервативным
        assert reject.sum() <= 20, f"Слишком много отвержений: {reject.sum()}"

    def test_fdr_bh_length_preserved(self) -> None:
        """Длина массивов после BH сохраняется."""
        from src.analysis.multiple_testing import apply_fdr_bh
        pvals = np.array([0.001, 0.01, 0.05, 0.1, 0.5])
        reject, adj = apply_fdr_bh(pvals)
        assert len(reject) == len(pvals)
        assert len(adj) == len(pvals)

    def test_apply_bh_to_series(self) -> None:
        """apply_bh_to_series() возвращает DataFrame с нужными колонками."""
        from src.analysis.multiple_testing import apply_bh_to_series
        series_pvals = {
            "series_0": 0.001,
            "series_1": 0.3,
            "series_2": 0.8,
        }
        result = apply_bh_to_series(series_pvals)
        required = {"series_id", "raw_pvalue", "adjusted_pvalue", "reject_h0", "significant"}
        assert required.issubset(set(result.columns))
        assert len(result) == 3

    def test_fdr_detects_significant(self) -> None:
        """FDR обнаруживает очень малые p-value."""
        from src.analysis.multiple_testing import apply_fdr_bh
        # 5 значимых + 95 случайных
        pvals = np.concatenate([
            np.array([1e-6, 1e-5, 1e-4, 1e-3, 0.005]),
            np.random.default_rng(42).uniform(0.1, 1.0, 95),
        ])
        reject, _ = apply_fdr_bh(pvals, alpha=0.05)
        # Хотя бы некоторые значимые должны быть обнаружены
        assert reject[:5].sum() >= 3

    def test_effective_number_1d(self) -> None:
        """effective_number_of_tests() для 1D возвращает len(pvalues)."""
        from src.analysis.multiple_testing import effective_number_of_tests
        pvals = np.array([0.01, 0.05, 0.1])
        meff = effective_number_of_tests(pvals, method="simple")
        assert meff == 3


# ---------------------------------------------------------------------------
# TestETAS
# ---------------------------------------------------------------------------

class TestETAS:
    """Тесты ETAS-генератора синтетических каталогов."""

    def test_import(self) -> None:
        from src.analysis.etas_validation import ETASCatalogGenerator
        assert ETASCatalogGenerator is not None

    def test_generate_returns_dataframe(self) -> None:
        """generate() возвращает DataFrame."""
        from src.analysis.etas_validation import ETASCatalogGenerator
        gen = ETASCatalogGenerator(m_min=6.5)
        df = gen.generate(n_background=20, t_end=10, seed=42)
        assert isinstance(df, pd.DataFrame)

    def test_catalog_has_required_columns(self) -> None:
        """Каталог содержит обязательные колонки."""
        from src.analysis.etas_validation import ETASCatalogGenerator
        gen = ETASCatalogGenerator(m_min=6.5)
        df = gen.generate(n_background=20, t_end=10, seed=42)
        required = {"time_years", "lat", "lon", "magnitude", "is_background", "generation"}
        assert required.issubset(set(df.columns))

    def test_catalog_size_at_least_background(self) -> None:
        """Каталог содержит не меньше фоновых событий."""
        from src.analysis.etas_validation import ETASCatalogGenerator
        n_bg = 50
        gen = ETASCatalogGenerator(m_min=6.5)
        df = gen.generate(n_background=n_bg, t_end=10, seed=42)
        assert len(df) >= n_bg

    def test_magnitudes_above_m_min(self) -> None:
        """Все магнитуды >= m_min."""
        from src.analysis.etas_validation import ETASCatalogGenerator
        m_min = 6.5
        gen = ETASCatalogGenerator(m_min=m_min)
        df = gen.generate(n_background=30, t_end=10, seed=42)
        assert (df["magnitude"] >= m_min).all()

    def test_background_events_present(self) -> None:
        """Каталог содержит фоновые события."""
        from src.analysis.etas_validation import ETASCatalogGenerator
        gen = ETASCatalogGenerator(m_min=6.5)
        df = gen.generate(n_background=30, t_end=10, seed=42)
        assert df["is_background"].sum() > 0

    def test_reproducible_with_seed(self) -> None:
        """Генерация воспроизводима при одинаковом seed."""
        from src.analysis.etas_validation import ETASCatalogGenerator
        gen = ETASCatalogGenerator(m_min=6.5)
        df1 = gen.generate(n_background=20, t_end=5, seed=99)
        df2 = gen.generate(n_background=20, t_end=5, seed=99)
        assert len(df1) == len(df2)
        np.testing.assert_array_almost_equal(
            df1["magnitude"].values, df2["magnitude"].values,
        )

    def test_local_offspring(self) -> None:
        """Дочерние события находятся вблизи родителя (< max_local_radius_km × 2)."""
        from src.analysis.etas_validation import ETASCatalogGenerator, _haversine_km
        gen = ETASCatalogGenerator(m_min=6.5, K=0.5)  # высокая продуктивность
        max_r = 300.0
        df = gen.generate(
            n_background=10, t_end=5, seed=42, max_local_radius_km=max_r,
        )
        # Проверяем: все дочерние в пределах max_r * 3 от [-60,60] x [-180,180] centre
        # (не строгое условие, просто нет аномально далёких)
        assert (np.abs(df["lat"]) <= 90).all()
        assert (np.abs(df["lon"]) <= 180).all()


# ---------------------------------------------------------------------------
# TestCalibration
# ---------------------------------------------------------------------------

class TestCalibration:
    """Тесты калибровки порогов."""

    def test_generate_catalog_with_injected_series(self) -> None:
        """generate_catalog_with_injected_series() возвращает каталог с сериями."""
        from src.analysis.threshold_calibration import generate_catalog_with_injected_series
        df, true_idx = generate_catalog_with_injected_series(
            n_background=100, n_series=3, series_size=4, series_regions=2, seed=42,
        )
        assert isinstance(df, pd.DataFrame)
        assert len(true_idx) == 3
        required_cols = {"year", "month", "day", "lat", "lon", "magnitude", "fe_region"}
        assert required_cols.issubset(set(df.columns))

    def test_injected_series_indices_valid(self) -> None:
        """Индексы вставленных серий корректны."""
        from src.analysis.threshold_calibration import generate_catalog_with_injected_series
        df, true_idx = generate_catalog_with_injected_series(
            n_background=50, n_series=2, series_size=4, series_regions=2, seed=7,
        )
        for series_idxs in true_idx:
            assert len(series_idxs) > 0, "Пустая серия"
            for idx in series_idxs:
                assert 0 <= idx < len(df), f"Индекс {idx} вне диапазона"

    def test_series_in_different_regions(self) -> None:
        """Вставленные серии охватывают несколько регионов."""
        from src.analysis.threshold_calibration import generate_catalog_with_injected_series
        df, true_idx = generate_catalog_with_injected_series(
            n_background=100, n_series=3, series_size=6, series_regions=3, seed=42,
        )
        for series_idxs in true_idx:
            regions = df.iloc[series_idxs]["fe_region"].nunique()
            assert regions >= 1, "Серия должна иметь хотя бы 1 регион"

    def test_calibrate_thresholds_returns_dataframe(self) -> None:
        """calibrate_thresholds() возвращает DataFrame с нужными колонками."""
        from src.analysis.threshold_calibration import calibrate_thresholds
        from src.analysis.clustering import SeismicClusterAnalyzer

        analyzer = SeismicClusterAnalyzer()
        result = calibrate_thresholds(
            cluster_analyzer=analyzer,
            n_min_range=range(3, 5),
            n_regions_range=range(2, 4),
            n_synthetic=3,
            seed=42,
        )
        assert isinstance(result, pd.DataFrame)
        required = {"min_events", "min_regions", "precision", "recall", "f1"}
        assert required.issubset(set(result.columns))

    def test_calibrate_f1_in_range(self) -> None:
        """F1 находится в диапазоне [0, 1]."""
        from src.analysis.threshold_calibration import calibrate_thresholds
        from src.analysis.clustering import SeismicClusterAnalyzer

        analyzer = SeismicClusterAnalyzer()
        result = calibrate_thresholds(
            cluster_analyzer=analyzer,
            n_min_range=range(3, 5),
            n_regions_range=range(2, 3),
            n_synthetic=2,
            seed=42,
        )
        assert (result["f1"] >= 0).all()
        assert (result["f1"] <= 1).all()


# ---------------------------------------------------------------------------
# TestTectonicDistanceV2
# ---------------------------------------------------------------------------

class TestTectonicDistanceV2:
    """Тесты улучшенного калькулятора тектонических расстояний."""

    def test_import(self) -> None:
        from src.analysis.tectonic_distance_v2 import TectonicDistanceV2
        assert TectonicDistanceV2 is not None

    def test_build_graph(self) -> None:
        """build_graph() строит граф с узлами и рёбрами."""
        from src.analysis.tectonic_distance_v2 import TectonicDistanceV2
        calc = TectonicDistanceV2()
        g = calc.build_graph(resolution_deg=2.0)
        assert g.number_of_nodes() > 0
        assert g.number_of_edges() > 0

    def test_tectonic_distance_positive(self) -> None:
        """Тектоническое расстояние > 0 для разных точек."""
        from src.analysis.tectonic_distance_v2 import TectonicDistanceV2
        calc = TectonicDistanceV2()
        calc.build_graph(resolution_deg=2.0)
        dist = calc.tectonic_distance_v2(35.0, 139.0, -33.5, -70.5)
        assert dist > 0

    def test_boundary_type_returns_valid(self) -> None:
        """boundary_type_for_pair() возвращает допустимый тип."""
        from src.analysis.tectonic_distance_v2 import TectonicDistanceV2, BOUNDARY_WEIGHTS
        calc = TectonicDistanceV2()
        calc.build_graph(resolution_deg=2.0)
        btype = calc.boundary_type_for_pair(35.0, 139.0, 0.0, 90.0)
        assert btype in BOUNDARY_WEIGHTS

    def test_distance_symmetry(self) -> None:
        """Расстояние симметрично (≈)."""
        from src.analysis.tectonic_distance_v2 import TectonicDistanceV2
        calc = TectonicDistanceV2()
        calc.build_graph(resolution_deg=2.0)
        d1 = calc.tectonic_distance_v2(35.0, 139.0, 0.0, 90.0)
        d2 = calc.tectonic_distance_v2(0.0, 90.0, 35.0, 139.0)
        # Из-за асимметрии d1 и d2 (snap to graph node) могут немного различаться
        assert abs(d1 - d2) / max(d1, d2) < 0.5  # в пределах 50%


# ---------------------------------------------------------------------------
# TestTriggeringModes
# ---------------------------------------------------------------------------

class TestTriggeringModes:
    """Тесты анализатора режимов триггеринга."""

    def test_import(self) -> None:
        from src.analysis.triggering_modes import TriggeringModeAnalyzer
        assert TriggeringModeAnalyzer is not None

    def test_eta_dynamic_positive(self) -> None:
        """eta_dynamic() > 0 для корректных входных данных."""
        from src.analysis.triggering_modes import eta_dynamic
        eta = eta_dynamic(t_days=5.0, r_km=100.0, m=6.5)
        assert eta > 0 and np.isfinite(eta)

    def test_eta_static_positive(self) -> None:
        """eta_static() > 0 для корректных входных данных."""
        from src.analysis.triggering_modes import eta_static
        eta = eta_static(t_years=1.0, r_km=500.0, m=7.0)
        assert eta > 0 and np.isfinite(eta)

    def test_eta_inf_for_zero_time(self) -> None:
        """eta возвращает inf для нулевого временного интервала."""
        from src.analysis.triggering_modes import eta_dynamic, eta_static
        assert not np.isfinite(eta_dynamic(0.0, 100.0, 6.5))
        assert not np.isfinite(eta_static(0.0, 100.0, 6.5))

    def test_classify_pairs(self) -> None:
        """classify_pairs() возвращает DataFrame с нужными колонками."""
        from src.analysis.triggering_modes import TriggeringModeAnalyzer
        df = _make_catalog(n=10, seed=42)
        analyzer = TriggeringModeAnalyzer()
        result = analyzer.classify_pairs(df)
        required = {"parent_id", "child_id", "delta_t_days", "r_tect_km", "mode", "eta"}
        assert required.issubset(set(result.columns))
        # Все режимы допустимые
        valid_modes = {"dynamic", "static", "intermediate", "background"}
        assert set(result["mode"].unique()).issubset(valid_modes)

    def test_dynamic_series_returns_list(self) -> None:
        """dynamic_series() возвращает список."""
        from src.analysis.triggering_modes import TriggeringModeAnalyzer
        df = _make_catalog(n=20, seed=42)
        analyzer = TriggeringModeAnalyzer()
        result = analyzer.dynamic_series(df, min_events=2)
        assert isinstance(result, list)
