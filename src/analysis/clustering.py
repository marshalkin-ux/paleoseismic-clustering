"""Кластеризация глобальных сейсмических серий.

End-to-end detector (see paper §3.3, ``pipeline_v2.py``):

1. Gardner–Knopoff declustering → mainshocks (primary; ZBZ/none sensitivity-tested)
2. Baiesi–Paczuski η NN forest (b=1.0, r^1.6 — BP 2004; **r_ij = great-circle km**)
3. ``global_series()`` sliding windows (1/2/5 yr); primary gate mean pairwise GC > 1500 km
4. Permutation (mean log10 η_NN) and ETAS-null validation

Tectonic-path distance (Bird 2003) is **deprecated for inference** — diagnostic only
(98% GC fallback; see ``tectonic_distance_v2.py``). Series detection never used it.

Output: algorithmic candidates, not validated physical series.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Callable

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Параметры метрики Baiesi-Paczuski
DF_DEFAULT = 1.6   # фрактальная размерность
B_DEFAULT = 1.0    # b-value (наклон закона Gutenberg-Richter)
SECS_PER_YEAR = 365.25 * 24 * 3600

# Primary global-series spatial gate: mean pairwise great-circle distance (km)
DEFAULT_MIN_MEAN_GC_KM = 1500.0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance (km)."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(a, 0.0, 1.0)))


def mean_pairwise_gc_km(lats: np.ndarray, lons: np.ndarray) -> float:
    """Mean great-circle distance over all unordered event pairs."""
    n = len(lats)
    if n < 2:
        return 0.0
    total = 0.0
    count = 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            total += _haversine_km(lats[i], lons[i], lats[j], lons[j])
            count += 1
    return total / count if count else 0.0


def _eta_metric(
    t_ij: float,
    r_ij: float,
    m_i: float,
    df: float = DF_DEFAULT,
    b: float = B_DEFAULT,
) -> float:
    """Метрика связи Baiesi-Paczuski (2004).

    eta_ij = t_ij * r_ij^df * 10^(-b * m_i)

    Args:
        t_ij: временной интервал в годах (t_j - t_i > 0).
        r_ij: тектоническое расстояние в км.
        m_i: магнитуда родительского события i.
        df: фрактальная размерность.
        b: b-value.

    Returns:
        Значение метрики eta (меньше = теснее связаны).
    """
    if t_ij <= 0 or r_ij <= 0:
        return np.inf
    return t_ij * (r_ij ** df) * (10 ** (-b * m_i))


# Alias for backward compatibility with tests and monte_carlo
_eta = _eta_metric


def _events_to_time_years(df: pd.DataFrame) -> np.ndarray:
    """Преобразует year/month/day в числовое время (годы)."""
    year = df["year"].fillna(0).astype(float).values
    month = df["month"].fillna(6).astype(float).values
    day = df["day"].fillna(15).astype(float).values
    return year + (month - 1) / 12.0 + (day - 1) / 365.25


class SeismicClusterAnalyzer:
    """Анализатор кластеров глобальных сейсмических серий.

    Реализует метрику Baiesi-Paczuski для идентификации кластеров
    и поиска глобальных серий (события M>=6.5 в разных регионах
    в одном временном окне).

    Пример::

        analyzer = SeismicClusterAnalyzer()
        df_with_parents = analyzer.find_nearest_neighbor(df, dist_fn)
        clusters = analyzer.identify_clusters(df_with_parents, eta_threshold=1e-5)
    """

    def __init__(
        self,
        df_param: float = DF_DEFAULT,
        b_param: float = B_DEFAULT,
        dist_calculator=None,
    ) -> None:
        self.df_param = df_param
        self.b_param = b_param
        self.dist_calculator = dist_calculator

    def find_nearest_neighbor(
        self,
        df: pd.DataFrame,
        dist_calculator=None,
        tectonic_dist_fn: Callable[[float, float, float, float], float] | None = None,
    ) -> pd.DataFrame:
        """Для каждого события находит ближайшего «родителя» по метрике eta.

        Событие j считает i своим родителем, если i предшествует j
        и имеет минимальное значение eta_ij.

        Args:
            df: DataFrame с колонками time/latitude/longitude/magnitude
                или year/month/day/lat/lon/magnitude.
            dist_calculator: TectonicDistanceCalculator (предпочтительно).
            tectonic_dist_fn: альтернативная функция расстояния
                              (lat1,lon1,lat2,lon2)->km.

        Returns:
            DataFrame с добавленными колонками: parent_id, eta.
        """
        from .tectonic_distance import _haversine_km

        # Разрешаем dist_calculator из __init__ если не передан явно
        if dist_calculator is None:
            dist_calculator = self.dist_calculator

        # Определяем функцию расстояния
        if dist_calculator is not None:
            def _dist_fn(la1, lo1, la2, lo2):
                return dist_calculator.tectonic_distance(la1, lo1, la2, lo2)
        elif tectonic_dist_fn is not None:
            _dist_fn = tectonic_dist_fn
        else:
            def _dist_fn(la1, lo1, la2, lo2):
                return _haversine_km(la1, lo1, la2, lo2) * 1.5

        df = df.copy().reset_index(drop=True)

        # Поддержка обоих форматов колонок координат
        lat_col = "latitude" if "latitude" in df.columns else "lat"
        lon_col = "longitude" if "longitude" in df.columns else "lon"

        # Время: datetime-колонка 'time' или числовое из year/month/day
        if "time" in df.columns:
            df = df.sort_values("time").reset_index(drop=True)
            t_datetime = pd.to_datetime(df["time"])
            t_ref = t_datetime.iloc[0]
            times = np.array(
                [(t - t_ref).total_seconds() / (365.25 * 86400) for t in t_datetime]
            )
        else:
            times = _events_to_time_years(df)

        lats = df[lat_col].fillna(0).values
        lons = df[lon_col].fillna(0).values
        mags = df["magnitude"].fillna(6.5).values

        parent_ids = np.full(len(df), np.nan)
        etas = np.full(len(df), np.nan)

        for j in range(1, len(df)):
            best_eta = np.inf
            best_i = -1
            for i in range(j):
                t_ij = times[j] - times[i]
                if t_ij <= 0:
                    continue
                try:
                    r_ij = _dist_fn(lats[i], lons[i], lats[j], lons[j])
                except Exception:
                    r_ij = _haversine_km(lats[i], lons[i], lats[j], lons[j]) * 1.5

                eta = _eta_metric(t_ij, r_ij, mags[i], self.df_param, self.b_param)
                if eta < best_eta:
                    best_eta = eta
                    best_i = i

            if best_i >= 0:
                parent_ids[j] = float(best_i)
                etas[j] = best_eta

        df["parent_id"] = parent_ids
        df["eta"] = etas
        # Legacy column aliases for backward-compat code
        df["parent_idx"] = np.where(np.isnan(parent_ids), -1, parent_ids.astype(int))
        df["eta_nn"] = np.where(np.isnan(etas), np.inf, etas)
        return df

    def identify_clusters(
        self,
        df: pd.DataFrame,
        eta_threshold: float | None = None,
    ) -> pd.DataFrame:
        """Выделяет кластеры по порогу метрики eta.

        События с eta < eta_threshold объединяются со своим родителем
        в один кластер. Изолированные события (eta >= threshold) образуют
        фоновую сейсмичность (cluster_id = 0).

        Args:
            df: DataFrame с колонками parent_id, eta (из find_nearest_neighbor).
            eta_threshold: порог в пространстве eta. Если None, используется
                           10^(медиана log10(eta)) — автоматический выбор.

        Returns:
            DataFrame с добавленной колонкой cluster_id
            (0 = фоновое событие, >0 = номер кластера).
        """
        df = df.copy().reset_index(drop=True)
        n = len(df)

        # Определяем имена колонок (поддержка обоих форматов)
        pid_col = "parent_id" if "parent_id" in df.columns else "parent_idx"
        eta_col = "eta" if "eta" in df.columns else "eta_nn"

        etas = df[eta_col].values
        valid_etas = etas[~np.isnan(etas) & ~np.isinf(etas) & (etas > 0)]

        if eta_threshold is None:
            if len(valid_etas) > 0:
                eta_threshold = float(10 ** np.median(np.log10(valid_etas)))
            else:
                eta_threshold = 1e-5

        cluster_id = np.full(n, -1, dtype=int)

        # Union-Find для объединения кластеров
        uf_parent = list(range(n))

        def find(x: int) -> int:
            while uf_parent[x] != x:
                uf_parent[x] = uf_parent[uf_parent[x]]
                x = uf_parent[x]
            return x

        def union(x: int, y: int) -> None:
            rx, ry = find(x), find(y)
            if rx != ry:
                uf_parent[ry] = rx

        for j in range(n):
            raw_pid = df.loc[j, pid_col]
            if pd.isna(raw_pid):
                continue
            p_idx = int(raw_pid)
            if p_idx < 0:
                continue
            eta = float(df.loc[j, eta_col])
            if not np.isnan(eta) and not np.isinf(eta) and eta < eta_threshold:
                union(p_idx, j)

        # Присваиваем cluster_id через корень дерева (0-based, -1 = фон)
        root_to_cluster: dict[int, int] = {}
        next_cluster = 0
        for j in range(n):
            root = find(j)
            has_connection = any(
                find(k) == root and k != j
                for k in range(n)
            )
            if has_connection:
                if root not in root_to_cluster:
                    root_to_cluster[root] = next_cluster
                    next_cluster += 1
                cluster_id[j] = root_to_cluster[root]

        # Сбрасываем кластеры с < 2 событий обратно в фон (-1)
        counts: dict[int, int] = defaultdict(int)
        for cid in cluster_id:
            if cid >= 0:
                counts[cid] += 1

        for j in range(n):
            if cluster_id[j] >= 0 and counts[cluster_id[j]] < 2:
                cluster_id[j] = -1

        df["cluster_id"] = cluster_id
        n_clusters = len([c for c in counts if counts[c] >= 2])
        n_bg = int(np.sum(cluster_id == -1))
        logger.info(
            "Идентифицировано %d кластеров, %d фоновых событий",
            n_clusters, n_bg,
        )
        return df

    def sliding_window_density(
        self,
        df: pd.DataFrame,
        window_sizes: list[int] | None = None,
    ) -> pd.DataFrame:
        """Вычисляет плотность событий в скользящих временных окнах.

        Args:
            df: DataFrame с колонкой year, month, day, magnitude.
            window_sizes: список размеров окон в днях.

        Returns:
            DataFrame с колонками времени и плотности для каждого окна.
        """
        if window_sizes is None:
            window_sizes = [1, 7, 30, 365, 3650]

        times = _events_to_time_years(df)
        t_min, t_max = times.min(), times.max()
        t_grid = np.linspace(t_min, t_max, 1000)

        result = pd.DataFrame({"time_years": t_grid})

        for ws in window_sizes:
            ws_years = ws / 365.25
            densities = np.zeros(len(t_grid))
            for k, t in enumerate(t_grid):
                mask = (times >= t - ws_years / 2) & (times < t + ws_years / 2)
                densities[k] = np.sum(mask)
            result[f"density_{ws}d"] = densities / ws_years

        return result

    def global_series(
        self,
        df: pd.DataFrame,
        time_window_years: float = 1.0,
        min_events: int = 4,
        min_magnitude: float = 6.5,
        min_mean_gc_km: float = DEFAULT_MIN_MEAN_GC_KM,
        min_regions: int | None = None,
    ) -> list[pd.DataFrame]:
        """Ищет глобальные серии в скользящих временных окнах.

        Primary gate: mean pairwise great-circle distance among window events
        exceeds ``min_mean_gc_km`` (default 1500 km). Flinn--Engdahl region
        count is recorded when ``fe_region`` is present but is **not** a gate
        unless ``min_regions`` is set explicitly (diagnostic / legacy).

        Args:
            df: DataFrame with year, magnitude, lat/lon; fe_region optional.
            time_window_years: sliding window width (years).
            min_events: minimum events per candidate series.
            min_magnitude: magnitude cutoff.
            min_mean_gc_km: minimum mean pairwise GC distance (km).
            min_regions: optional FE-region gate (legacy); None = diagnostic only.

        Returns:
            List of DataFrames, one per merged global-series candidate.
        """
        lat_col = "latitude" if "latitude" in df.columns else "lat"
        lon_col = "longitude" if "longitude" in df.columns else "lon"

        required = ["year", "magnitude", lat_col, lon_col]
        if any(c not in df.columns for c in required):
            logger.warning("Missing columns for global_series: %s", required)
            return []

        sub = df[df["magnitude"] >= min_magnitude].copy()
        sub = sub.rename(columns={lat_col: "lat", lon_col: "lon"})
        sub = sub.dropna(subset=["year", "lat", "lon"])
        sub = sub.sort_values(["year", "month", "day"]).reset_index(drop=True)

        times = _events_to_time_years(sub)
        series_list: list[pd.DataFrame] = []
        used = np.zeros(len(sub), dtype=bool)

        for i in range(len(sub)):
            if used[i]:
                continue
            window_mask = (times >= times[i]) & (times < times[i] + time_window_years)
            window_events = sub[window_mask].copy()

            if len(window_events) < min_events:
                continue

            lats = window_events["lat"].astype(float).values
            lons = window_events["lon"].astype(float).values
            mean_gc = mean_pairwise_gc_km(lats, lons)

            if mean_gc < min_mean_gc_km:
                continue

            if min_regions is not None and "fe_region" in window_events.columns:
                if window_events["fe_region"].nunique() < min_regions:
                    continue

            window_events["mean_pairwise_gc_km"] = mean_gc
            if "fe_region" in window_events.columns:
                window_events["n_fe_regions"] = int(
                    window_events["fe_region"].nunique()
                )
            window_events["series_anchor_year"] = int(sub.loc[i, "year"])
            series_list.append(window_events)
            used[np.asarray(window_mask)] = True
            n_reg = (
                int(window_events["fe_region"].nunique())
                if "fe_region" in window_events.columns
                else -1
            )
            logger.debug(
                "Global series: %d events, mean GC=%.0f km, %d FE regions, ~%d",
                len(window_events), mean_gc, n_reg, int(sub.loc[i, "year"]),
            )

        logger.debug("Найдено %d глобальных серий (mean GC > %.0f km)", len(series_list), min_mean_gc_km)
        return series_list
