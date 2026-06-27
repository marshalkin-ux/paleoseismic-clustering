"""Генерация синтетических ETAS-каталогов и валидация алгоритма.

ETAS (Epidemic Type Aftershock Sequence) — стандартная статистическая модель
сейсмичности. Генерация синтетических каталогов позволяет оценить
частоту ложных открытий алгоритма кластеризации.

Параметры по умолчанию откалиброваны для глобального каталога M≥6.5:
- mu=0.008: фоновая интенсивность ~1 событие/нед/глобально
- K=0.08, alpha=1.0: продуктивность афтершоков (Helmstetter & Sornette 2003)
- c=0.005, p=1.1: параметры Омори-Уцу
- max_trigger_distance_km=500: только локальные триггеры

Ссылки: Ogata (1988, 1998), Helmstetter & Sornette (2002, 2003).
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from src.curator.unifier import FE_REGIONS

logger = logging.getLogger(__name__)

_R_EARTH = 6371.0  # км
_FE_COORDS = np.array([(r[2], r[3]) for r in FE_REGIONS])
_FE_TREE = cKDTree(_FE_COORDS)


def assign_fe_regions(df: pd.DataFrame) -> pd.DataFrame:
    """Назначает номера регионов Flinn-Engdahl по координатам (KD-tree)."""
    coords = df[["lat", "lon"]].fillna(0).values
    _, indices = _FE_TREE.query(coords)
    out = df.copy()
    out["fe_region"] = [FE_REGIONS[i][0] for i in indices]
    return out


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Расстояние по формуле гаверсинуса (км)."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * _R_EARTH * np.arcsin(np.sqrt(a))


def etas_omori_sample(
    n: int,
    c: float,
    p: float,
    t_max: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Выборка времён из распределения Омори-Уцу через inverse CDF.

    CDF при p≠1:  F(t) = 1 - ((t+c)/c)^(1-p)
    Inverse:       t = c * (1-u)^(1/(1-p)) - c

    При p≈1 используется логарифмическое приближение.

    Args:
        n: число выборок.
        c: временной сдвиг (дни).
        p: показатель Омори (обычно 1.0–1.3).
        t_max: максимальное время (дни); результат обрезается.
        rng: генератор случайных чисел NumPy.

    Returns:
        Массив времён формы (n,), все значения в [0, t_max].
    """
    if abs(p - 1.0) < 1e-6:
        # Логарифмическое распределение при p→1: τ ~ c * exp(Exp(1)/c) - c
        # Точная инверсия: CDF = 1 - exp(-t/c), τ = -c * ln(u)
        u = rng.uniform(0.0, 1.0, n)
        times = -c * np.log(np.clip(u, 1e-15, 1.0))
    else:
        u = rng.uniform(0.0, 1.0, n)
        times = c * np.power(np.clip(1.0 - u, 1e-15, 1.0), 1.0 / (1.0 - p)) - c

    return np.clip(times, 0.0, t_max)


class ETASCatalogGenerator:
    """ETAS-каталог с параметрами глобальной сейсмичности (Ogata 1988, Helmstetter & Sornette 2003).

    Модель ETAS описывает условную интенсивность λ(t, x, y)::

        λ(t, x, y) = μ + Σ_{i: t_i<t} K·10^{α(m_i-M_0)} · (t-t_i+c)^{-p} · (r²+d²)^{-q}

    Параметры по умолчанию откалиброваны для глобального каталога M≥6.5:

    - mu=0.008: фоновая интенсивность ~1 событие/нед/глобально
    - K=0.08, alpha=1.0: продуктивность афтершоков (Helmstetter & Sornette 2003)
    - c=0.005 дней, p=1.1: параметры Омори-Уцу (Ogata 1988)
    - max_trigger_distance_km=500: КЛЮЧЕВОЕ — только локальные триггеры

    Алгоритм генерации (ветвящийся пуассоновский процесс):

    1. Генерировать фоновые события: Poisson(mu*T), равномерно в пространстве и времени.
    2. Для каждого события i: число потомков N_i ~ Poisson(K * 10^(alpha*(m_i - M0))).
    3. Время потомков: Омори-Уцу, P(t) ∝ (t+c)^{-p}, через inverse CDF.
    4. Координаты потомков: в радиусе max_trigger_distance_km от родителя.
    5. Магнитуды потомков: экспоненциально с b-value (Гутенберг-Рихтер).
    6. Рекурсивно для потомков потомков (до max_generation=5 поколений).
    7. Связи > max_trigger_distance_km ЗАПРЕЩЕНЫ → нет глобальных серий в синтетике.

    Ссылки: Ogata (1988, 1998), Helmstetter & Sornette (2002, 2003).
    """

    def __init__(
        self,
        mu: float = 0.008,           # фоновая интенсивность (~1 событие/нед/глобально)
        K: float = 0.08,             # продуктивность афтершоков (Helmstetter & Sornette 2003)
        alpha: float = 1.0,          # зависимость продуктивности от магнитуды
        c: float = 0.005,            # параметр Omori (дни; Ogata 1988)
        p: float = 1.1,              # показатель Omori (Ogata 1988)
        d: float = 10.0,             # пространственный масштаб (км)
        q: float = 1.5,              # пространственный показатель
        m_min: float = 6.5,          # минимальная магнитуда каталога
        b: float = 1.0,              # b-value GR
        max_trigger_distance_km: float = 500.0,  # ключевое ограничение локальности
    ) -> None:
        """
        Args:
            mu: фоновая интенсивность (события/день на единицу площади).
            K: продуктивность афтершоков (ожидаемое число дочерних событий).
            alpha: усиление продуктивности с магнитудой.
            c: параметр времени в законе Omori (дни).
            p: показатель закона Omori (> 1).
            d: пространственный масштаб (км).
            q: пространственный показатель (> 1).
            m_min: минимальная регистрируемая магнитуда.
            b: наклон закона Гутенберга-Рихтера.
            max_trigger_distance_km: максимальное расстояние триггеринга (км).
        """
        self.mu = mu
        self.K = K
        self.alpha = alpha
        self.c = c
        self.p = p
        self.d = d
        self.q = q
        self.m_min = m_min
        self.b = b
        self.max_trigger_distance_km = max_trigger_distance_km

    def _sample_magnitude(self, rng: np.random.Generator, n: int) -> np.ndarray:
        """Выборка магнитуд из распределения Гутенберга-Рихтера."""
        # P(M > m) = 10^(-b*(m - m_min))  =>  M = m_min - log10(U) / b
        u = rng.uniform(0, 1, n)
        return self.m_min - np.log10(u + 1e-15) / self.b

    def _n_offspring(self, magnitude: float, rng: np.random.Generator) -> int:
        """Число прямых потомков события с данной магнитудой."""
        lam = self.K * 10 ** (self.alpha * (magnitude - self.m_min))
        return int(rng.poisson(lam))

    def _sample_offspring_time(self, parent_time: float, rng: np.random.Generator) -> float:
        """Время потомка из закона Omori-Utsu (дни после родителя)."""
        # Инверсия CDF: τ = c * ((1 - u)^(-1/(p-1)) - 1)
        u = rng.uniform(0, 1)
        if self.p == 1.0:
            # Вырожденный случай — экспоненциальное распределение
            tau = -self.c * np.log(u + 1e-15)
        else:
            tau = self.c * ((1 - u) ** (-1.0 / (self.p - 1)) - 1)
        return parent_time + max(tau, 0.0)

    def _sample_offspring_location(
        self,
        parent_lat: float,
        parent_lon: float,
        max_radius_km: float,
        rng: np.random.Generator,
    ) -> tuple[float, float]:
        """Генерирует координаты потомка вблизи родителя.

        Использует распределение ~(r² + d²)^(-q).

        Args:
            parent_lat, parent_lon: координаты родителя.
            max_radius_km: ограничение на радиус (гарантирует локальность).
            rng: генератор случайных чисел.

        Returns:
            Кортеж (lat, lon) потомка.
        """
        # Генерация радиуса через инверсию CDF
        # P(R > r) ~ (r² + d²)^(-(q-1))
        max_iter = 100
        for _ in range(max_iter):
            u = rng.uniform(0, 1)
            if self.q > 1:
                r_km = self.d * np.sqrt(((1 - u) ** (-1.0 / (self.q - 1))) - 1)
            else:
                r_km = self.d * rng.exponential()

            if r_km <= max_radius_km:
                break
        else:
            r_km = rng.uniform(0, max_radius_km)

        # Случайный азимут
        azimuth = rng.uniform(0, 2 * np.pi)

        # Перемещение по поверхности Земли
        lat_rad = np.radians(parent_lat)
        angular_dist = r_km / _R_EARTH

        new_lat = np.degrees(
            np.arcsin(
                np.sin(lat_rad) * np.cos(angular_dist)
                + np.cos(lat_rad) * np.sin(angular_dist) * np.cos(azimuth)
            )
        )
        new_lon = parent_lon + np.degrees(
            np.arctan2(
                np.sin(azimuth) * np.sin(angular_dist) * np.cos(lat_rad),
                np.cos(angular_dist) - np.sin(lat_rad) * np.sin(np.radians(new_lat)),
            )
        )
        # Нормализация долготы
        new_lon = ((new_lon + 180) % 360) - 180
        return float(new_lat), float(new_lon)

    def generate(
        self,
        n_background: int = 80,
        t_start: float = 0.0,
        t_end: float = 50.0,
        lat_range: tuple[float, float] = (-60.0, 60.0),
        lon_range: tuple[float, float] = (-180.0, 180.0),
        max_local_radius_km: float | None = None,
        seed: int | None = None,
    ) -> pd.DataFrame:
        """Генерирует синтетический каталог ETAS через ветвящийся пуассоновский процесс.

        Ключевое ограничение: каждый потомок генерируется в пределах
        ``max_local_radius_km`` от родителя — гарантирует отсутствие глобальных серий.

        Args:
            n_background: число фоновых событий (Poisson(mu·T)).
            t_start: начало каталога (годы).
            t_end: конец каталога (годы).
            lat_range: диапазон широт.
            lon_range: диапазон долгот.
            max_local_radius_km: максимальный радиус для дочерних событий.
                Если None — используется ``self.max_trigger_distance_km``.
            seed: зерно генератора.

        Returns:
            DataFrame с колонками:
            ``time_years``, ``lat``, ``lon``, ``magnitude``,
            ``is_background``, ``generation``.
        """
        if max_local_radius_km is None:
            max_local_radius_km = self.max_trigger_distance_km

        rng = np.random.default_rng(seed)
        t_span_days = (t_end - t_start) * 365.25

        bg_times_days = rng.uniform(0, t_span_days, n_background)
        bg_lats = rng.uniform(lat_range[0], lat_range[1], n_background)
        bg_lons = rng.uniform(lon_range[0], lon_range[1], n_background)
        bg_mags = self._sample_magnitude(rng, n_background)

        records: list[dict] = []
        for i in range(n_background):
            records.append({
                "time_days": bg_times_days[i],
                "lat": bg_lats[i],
                "lon": bg_lons[i],
                "magnitude": bg_mags[i],
                "is_background": True,
                "generation": 0,
            })

        queue = list(zip(
            bg_times_days, bg_lats, bg_lons, bg_mags,
            [0] * n_background,
        ))

        max_generation = 5
        max_total = 50_000

        while queue and len(records) < max_total:
            parent_t, parent_lat, parent_lon, parent_mag, gen = queue.pop(0)

            if gen >= max_generation:
                continue

            n_off = self._n_offspring(parent_mag, rng)
            for _ in range(n_off):
                child_t = self._sample_offspring_time(parent_t, rng)
                if child_t > t_span_days:
                    continue

                child_lat, child_lon = self._sample_offspring_location(
                    parent_lat, parent_lon, max_local_radius_km, rng,
                )
                child_lat = float(np.clip(child_lat, lat_range[0], lat_range[1]))
                child_lon = float(np.clip(child_lon, lon_range[0], lon_range[1]))
                child_mag = float(self._sample_magnitude(rng, 1)[0])

                records.append({
                    "time_days": child_t,
                    "lat": child_lat,
                    "lon": child_lon,
                    "magnitude": child_mag,
                    "is_background": False,
                    "generation": gen + 1,
                })
                queue.append((child_t, child_lat, child_lon, child_mag, gen + 1))

        df = pd.DataFrame(records)
        df["time_years"] = t_start + df["time_days"] / 365.25
        df = df.sort_values("time_days").reset_index(drop=True)
        df = df.drop(columns=["time_days"])

        logger.info(
            "ETAS каталог: %d событий (%d фоновых, %d дочерних)",
            len(df),
            df["is_background"].sum(),
            (~df["is_background"]).sum(),
        )
        return df

    # ------------------------------------------------------------------
    # Вспомогательный метод для параллельной обработки
    # ------------------------------------------------------------------

    def _run_one_catalog(self, args: tuple) -> int:
        """Запускает кластеризацию на одном ETAS-каталоге."""
        i, seed_i, cluster_analyzer, min_events, time_window_years, n_background, t_end = args
        df = self.generate(n_background=n_background, t_end=t_end, seed=seed_i)
        df["year"] = df["time_years"].astype(int)
        df["month"] = (
            ((df["time_years"] - df["year"]) * 12) + 1
        ).astype(int).clip(1, 12)
        df["day"] = 15
        df = assign_fe_regions(df)
        found = cluster_analyzer.global_series(
            df,
            min_events=min_events,
            time_window_years=time_window_years,
        )
        return len(found)

    def run_false_positive_analysis(
        self,
        cluster_analyzer: Any,
        n_catalogs: int = 100,
        min_events: int = 4,
        time_window_years: float = 2.0,
        n_observed: int | None = None,
        n_workers: int | None = None,
        seed: int = 42,
        n_background: int = 80,
        t_span_years: float = 50.0,
    ) -> dict:
        """Параллельная ETAS-валидация: оценка частоты ложных открытий.

        Поскольку ETAS-каталоги содержат только локальные серии
        (``max_trigger_distance_km`` ≤ 500 км), любые «глобальные серии»,
        обнаруженные алгоритмом — ложные открытия.

        Алгоритм:
        1. Генерировать n_catalogs ETAS-каталогов (параллельно).
        2. На каждом запускать global_series() с заданными порогами.
        3. Возвращать распределение числа глобальных серий.

        Args:
            cluster_analyzer: ``SeismicClusterAnalyzer`` с методом ``global_series()``.
            n_catalogs: число синтетических каталогов.
            min_events: минимальное число событий в серии.
            time_window_years: временное окно (годы).
            n_observed: число серий в реальном каталоге (для p-value).
            n_workers: число рабочих процессов (None → cpu_count - 1).
            seed: начальное зерно.

        Returns:
            Словарь::

                {
                    'series_counts_per_catalog': list[int],  # число серий в каждом каталоге
                    'false_positive_rates': list[int],       # alias (backward compat)
                    'mean_false_series': float,
                    'std_false_series': float,
                    'max_false_series': int,
                    'p_value_empirical': float,              # P(N_etas >= N_observed)
                    'n_observed': int,
                    'n_catalogs': int,
                    'n_catalogs_with_false_series': int,     # каталоги с >= 1 серий
                    'false_positive_rate': float,            # n_catalogs_with_false / n_catalogs
                }
        """
        series_counts = np.zeros(n_catalogs, dtype=int)

        for i in range(n_catalogs):
            args = (
                i,
                seed + i,
                cluster_analyzer,
                min_events,
                time_window_years,
                n_background,
                t_span_years,
            )
            series_counts[i] = self._run_one_catalog(args)

        counts_list = series_counts.tolist()
        n_with_false = int(np.sum(series_counts > 0))
        mean_false = float(np.mean(series_counts))
        std_false = float(np.std(series_counts))
        fpr = float(n_with_false / n_catalogs)

        if n_observed is None:
            n_observed_val = 0
            p_value = float("nan")
        else:
            n_observed_val = int(n_observed)
            p_value = float(np.mean(series_counts >= n_observed_val))

        result = {
            "series_counts_per_catalog": counts_list,
            "false_positive_rates": counts_list,
            "mean_false_series": mean_false,
            "std_false_series": std_false,
            "max_false_series": int(np.max(series_counts)),
            "p_value_empirical": p_value,
            "n_observed": n_observed_val,
            "n_catalogs": n_catalogs,
            "n_catalogs_with_false_series": n_with_false,
            "false_positive_rate": fpr,
        }
        logger.info(
            "ETAS валидация: FPR=%.3f, mean=%.2f±%.2f, p=%.4f",
            fpr, mean_false, std_false, p_value if not np.isnan(p_value) else -1,
        )
        return result
