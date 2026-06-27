"""Разделение динамического и статического триггеринга.

Динамический триггеринг: сейсмические волны (Δt < 30 дней).
Статический триггеринг: перераспределение статических напряжений (Δt > 0.5 лет).

Основана на работах:
- Hill et al. (1993) — динамический триггеринг.
- King et al. (1994) — статическое изменение напряжений.
- Zaliapin & Ben-Zion (2013) — метрика ближайшего соседа.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Пороги режимов
# ---------------------------------------------------------------------------

DYNAMIC_THRESHOLD_DAYS: float = 30.0    # динамический: < 30 дней
STATIC_THRESHOLD_YEARS: float = 0.5    # статический: > 0.5 лет (≈ 182 дней)
STATIC_THRESHOLD_DAYS: float = STATIC_THRESHOLD_YEARS * 365.25

_SECS_PER_YEAR = 365.25 * 86400.0


def _get_lat_lon_cols(df: pd.DataFrame) -> tuple[str, str]:
    """Возвращает имена колонок широты и долготы."""
    lat = "latitude" if "latitude" in df.columns else "lat"
    lon = "longitude" if "longitude" in df.columns else "lon"
    return lat, lon


def _to_time_days(df: pd.DataFrame) -> np.ndarray:
    """Время в днях с начала каталога."""
    if "time" in df.columns:
        t = pd.to_datetime(df["time"])
        origin = t.iloc[0]
        return np.array([(x - origin).total_seconds() / 86400.0 for x in t])
    year = df["year"].fillna(0).astype(float).values
    month = df["month"].fillna(6).astype(float).values
    day = df["day"].fillna(15).astype(float).values
    return year * 365.25 + (month - 1) * 30.4375 + (day - 1)


# ---------------------------------------------------------------------------
# Метрики
# ---------------------------------------------------------------------------

def eta_dynamic(
    t_days: float,
    r_km: float,
    m: float,
    df: float = 1.6,
) -> float:
    """Метрика для динамического триггеринга (t < 30 дней).

    Время нормировано на 30 дней для сопоставимости с длинными интервалами:

        η_dyn = (t_days / 30) * r_km^df * 10^(-m)

    Args:
        t_days: временной интервал в днях (> 0).
        r_km: расстояние в км (> 0).
        m: магнитуда родительского события.
        df: фрактальная размерность.

    Returns:
        Значение метрики η (меньше = теснее связаны).
    """
    if t_days <= 0 or r_km <= 0:
        return np.inf
    t_norm = t_days / 30.0
    return t_norm * (r_km ** df) * (10 ** (-m))


def eta_static(
    t_years: float,
    r_km: float,
    m: float,
    df: float = 1.6,
) -> float:
    """Метрика для статического триггеринга (t > 0.5 лет).

    Стандартная η Baiesi-Paczuski в годах:

        η_stat = t_years * r_km^df * 10^(-b*m)

    Args:
        t_years: временной интервал в годах (> 0).
        r_km: расстояние в км (> 0).
        m: магнитуда родительского события.
        df: фрактальная размерность.

    Returns:
        Значение метрики η.
    """
    if t_years <= 0 or r_km <= 0:
        return np.inf
    return t_years * (r_km ** df) * (10 ** (-m))


# ---------------------------------------------------------------------------
# Классификатор режимов
# ---------------------------------------------------------------------------

class TriggeringModeAnalyzer:
    """Раздельный анализ динамического и статического триггеринга.

    Для каждого события определяется ближайший «родитель» в рамках
    каждого режима, затем пары классифицируются:

    - ``'dynamic'``: Δt < 30 дней.
    - ``'static'``: Δt > 0.5 лет (182 дней).
    - ``'intermediate'``: 30 дней ≤ Δt ≤ 182 дней.
    - ``'background'``: нет подходящего родителя в обоих режимах.
    """

    def __init__(
        self,
        df_param: float = 1.6,
        b_param: float = 1.0,
        dynamic_threshold_days: float = DYNAMIC_THRESHOLD_DAYS,
        static_threshold_years: float = STATIC_THRESHOLD_YEARS,
    ) -> None:
        """
        Args:
            df_param: фрактальная размерность.
            b_param: b-value.
            dynamic_threshold_days: верхняя граница для динамического режима (дни).
            static_threshold_years: нижняя граница для статического режима (годы).
        """
        self.df_param = df_param
        self.b_param = b_param
        self.dynamic_threshold_days = dynamic_threshold_days
        self.static_threshold_years = static_threshold_years
        self.static_threshold_days = static_threshold_years * 365.25

    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Гаверсинусное расстояние (км)."""
        _R = 6371.0
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        return 2 * _R * np.arcsin(np.sqrt(a))

    def _get_dist(self, lat1: float, lon1: float, lat2: float, lon2: float, dist_calc: Any) -> float:
        """Расстояние с приоритетом тектонического калькулятора."""
        if dist_calc is not None:
            try:
                return dist_calc.tectonic_distance(lat1, lon1, lat2, lon2)
            except Exception:
                pass
        return self._haversine_km(lat1, lon1, lat2, lon2) * 1.5

    def classify_pairs(
        self,
        df: pd.DataFrame,
        dist_calc: Any = None,
    ) -> pd.DataFrame:
        """Классифицирует пары (родитель, потомок) по режиму триггеринга.

        Для каждого события j находит лучшего родителя i в каждом режиме
        и выбирает наилучший (минимальный η).

        Args:
            df: DataFrame с координатами, временем и магнитудой.
            dist_calc: калькулятор расстояний (необязательно).

        Returns:
            DataFrame с колонками:
            ``parent_id``, ``child_id``, ``delta_t_days``,
            ``r_tect_km``, ``mode``, ``eta``.
        """
        df = df.copy().reset_index(drop=True)
        lat_col, lon_col = _get_lat_lon_cols(df)

        times_days = _to_time_days(df)
        lats = df[lat_col].values.astype(float)
        lons = df[lon_col].values.astype(float)
        mags = df["magnitude"].fillna(6.0).values.astype(float)

        records: list[dict] = []

        for j in range(1, len(df)):
            best_eta = np.inf
            best_i = -1
            best_mode = "background"
            best_dt = np.nan
            best_r = np.nan

            for i in range(j):
                dt_days = times_days[j] - times_days[i]
                if dt_days <= 0:
                    continue

                r_km = self._get_dist(lats[i], lons[i], lats[j], lons[j], dist_calc)

                # Определяем режим
                if dt_days < self.dynamic_threshold_days:
                    eta = eta_dynamic(dt_days, r_km, mags[i], self.df_param)
                    mode = "dynamic"
                elif dt_days > self.static_threshold_days:
                    t_years = dt_days / 365.25
                    eta = eta_static(t_years, r_km, mags[i], self.df_param)
                    mode = "static"
                else:
                    # Промежуточный — используем стандартную метрику
                    t_years = dt_days / 365.25
                    eta = eta_static(t_years, r_km, mags[i], self.df_param)
                    mode = "intermediate"

                if eta < best_eta:
                    best_eta = eta
                    best_i = i
                    best_mode = mode
                    best_dt = dt_days
                    best_r = r_km

            records.append({
                "parent_id": best_i if best_i >= 0 else None,
                "child_id": j,
                "delta_t_days": best_dt if best_i >= 0 else np.nan,
                "r_tect_km": best_r if best_i >= 0 else np.nan,
                "mode": best_mode,
                "eta": best_eta if np.isfinite(best_eta) else np.nan,
            })

        result = pd.DataFrame(records)
        logger.info(
            "Режимы триггеринга: dynamic=%d, static=%d, intermediate=%d, background=%d",
            (result["mode"] == "dynamic").sum(),
            (result["mode"] == "static").sum(),
            (result["mode"] == "intermediate").sum(),
            (result["mode"] == "background").sum(),
        )
        return result

    def dynamic_series(
        self,
        df: pd.DataFrame,
        min_events: int = 3,
        dist_calc: Any = None,
        max_radius_km: float = 2000.0,
    ) -> list[pd.DataFrame]:
        """Поиск серий через динамический механизм (окна 1–30 дней).

        Серия — группа событий, связанных цепочкой с Δt < 30 дней
        и расстоянием < max_radius_km.

        Args:
            df: DataFrame с координатами, временем и магнитудой.
            min_events: минимальный размер серии.
            dist_calc: калькулятор расстояний.
            max_radius_km: максимальный радиус для динамических связей.

        Returns:
            Список DataFrame, каждый — одна серия.
        """
        df = df.copy().reset_index(drop=True)
        lat_col, lon_col = _get_lat_lon_cols(df)

        times_days = _to_time_days(df)
        lats = df[lat_col].values.astype(float)
        lons = df[lon_col].values.astype(float)
        mags = df["magnitude"].fillna(6.0).values.astype(float)

        n = len(df)
        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: int, y: int) -> None:
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[ry] = rx

        for j in range(1, n):
            for i in range(j):
                dt = times_days[j] - times_days[i]
                if 0 < dt < self.dynamic_threshold_days:
                    r = self._get_dist(lats[i], lons[i], lats[j], lons[j], dist_calc)
                    if r < max_radius_km:
                        union(i, j)

        # Группировка
        from collections import defaultdict
        groups: dict[int, list[int]] = defaultdict(list)
        for idx in range(n):
            groups[find(idx)].append(idx)

        series = [
            df.iloc[indices].copy()
            for indices in groups.values()
            if len(indices) >= min_events
        ]
        logger.info("Динамические серии: найдено %d", len(series))
        return series

    def static_series(
        self,
        df: pd.DataFrame,
        min_events: int = 3,
        dist_calc: Any = None,
        max_radius_km: float = 5000.0,
        max_years: float = 10.0,
    ) -> list[pd.DataFrame]:
        """Поиск серий через статический механизм (окна 0.5–10 лет).

        Серия — группа событий, связанных цепочкой с 0.5 лет < Δt < max_years
        и расстоянием < max_radius_km.

        Args:
            df: DataFrame с координатами, временем и магнитудой.
            min_events: минимальный размер серии.
            dist_calc: калькулятор расстояний.
            max_radius_km: максимальный радиус.
            max_years: максимальный интервал (годы).

        Returns:
            Список DataFrame, каждый — одна серия.
        """
        df = df.copy().reset_index(drop=True)
        lat_col, lon_col = _get_lat_lon_cols(df)

        times_days = _to_time_days(df)
        lats = df[lat_col].values.astype(float)
        lons = df[lon_col].values.astype(float)

        n = len(df)
        max_days = max_years * 365.25
        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: int, y: int) -> None:
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[ry] = rx

        for j in range(1, n):
            for i in range(j):
                dt = times_days[j] - times_days[i]
                if self.static_threshold_days < dt < max_days:
                    r = self._get_dist(lats[i], lons[i], lats[j], lons[j], dist_calc)
                    if r < max_radius_km:
                        union(i, j)

        from collections import defaultdict
        groups: dict[int, list[int]] = defaultdict(list)
        for idx in range(n):
            groups[find(idx)].append(idx)

        series = [
            df.iloc[indices].copy()
            for indices in groups.values()
            if len(indices) >= min_events
        ]
        logger.info("Статические серии: найдено %d", len(series))
        return series
