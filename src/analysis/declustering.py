"""Декластеризация сейсмических каталогов.

Реализует два классических алгоритма выделения основных толчков:
- Gardner & Knopoff (1974) — метод временных и пространственных окон.
- Zaliapin & Ben-Zion (2013) — метод ближайшего соседа.
"""

from __future__ import annotations

import logging
from bisect import bisect_left
from typing import Sequence

import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

_R_EARTH = 6371.0  # км


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Расстояние по формуле гаверсинуса (км)."""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * _R_EARTH * np.arcsin(np.sqrt(a))


def _get_lat_lon_cols(df: pd.DataFrame) -> tuple[str, str]:
    """Возвращает имена колонок широты и долготы."""
    lat = "latitude" if "latitude" in df.columns else "lat"
    lon = "longitude" if "longitude" in df.columns else "lon"
    return lat, lon


def _to_time_days(df: pd.DataFrame) -> np.ndarray:
    """Преобразует временну́ю колонку в дни с начала каталога.

    Поддерживает как datetime-колонку ``time``, так и набор ``year/month/day``.
    """
    if "time" in df.columns:
        t = pd.to_datetime(df["time"])
        origin = t.iloc[0]
        return np.array([(x - origin).total_seconds() / 86400.0 for x in t])

    year = df["year"].fillna(0).astype(float).values
    month = df["month"].fillna(6).astype(float).values
    day = df["day"].fillna(15).astype(float).values
    return year * 365.25 + (month - 1) * 30.4375 + (day - 1)


# ---------------------------------------------------------------------------
# Gardner-Knopoff (1974)
# ---------------------------------------------------------------------------

class GardnerKnopoffDeclustering:
    """Декластеризация по методу Gardner & Knopoff (1974).

    Для каждого событий с магнитудой M определяются временно́е окно
    ``T(M)`` (дни) и пространственное окно ``R(M)`` (км) согласно
    таблице из оригинальной статьи. Все события, попавшие в это окно
    после главного толчка, считаются афтершоками.

    Алгоритм итерационный: рассматривает события по убыванию магнитуды,
    помечает события в окне как зависимые, затем переходит к следующему
    непомеченному событию.
    """

    # Оригинальная таблица Gardner & Knopoff (1974)
    # M -> (time_window_days, space_window_km)
    WINDOWS: dict[float, tuple[float, float]] = {
        2.5: (1.0, 19.5),
        3.0: (1.5, 22.5),
        3.5: (2.5, 26.0),
        4.0: (3.5, 30.0),
        4.5: (5.0, 35.0),
        5.0: (7.0, 40.0),
        5.5: (10.0, 47.0),
        6.0: (15.0, 54.0),
        6.5: (22.0, 61.0),
        7.0: (32.0, 70.0),
        7.5: (47.0, 81.0),
        8.0: (67.0, 94.0),
    }

    _M_KEYS: list[float] = sorted(WINDOWS.keys())

    def _get_window(self, m: float) -> tuple[float, float]:
        """Возвращает (time_days, space_km) для заданной магнитуды."""
        if m <= self._M_KEYS[0]:
            return self.WINDOWS[self._M_KEYS[0]]
        if m >= self._M_KEYS[-1]:
            return self.WINDOWS[self._M_KEYS[-1]]
        # Линейная интерполяция между ближайшими значениями
        idx = bisect_left(self._M_KEYS, m)
        m_lo, m_hi = self._M_KEYS[idx - 1], self._M_KEYS[idx]
        t_lo, r_lo = self.WINDOWS[m_lo]
        t_hi, r_hi = self.WINDOWS[m_hi]
        frac = (m - m_lo) / (m_hi - m_lo)
        return t_lo + frac * (t_hi - t_lo), r_lo + frac * (r_hi - r_lo)

    def decluster(
        self,
        df: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Разделяет каталог на главные толчки и афтершоки.

        Алгоритм (итерационный):
        1. Отсортировать по магнитуде (убывание).
        2. Для каждого непомеченного события определить окна T(M), R(M).
        3. Все последующие события в пространственно-временно́м окне —
           афтершоки.
        4. Предшествующие события в половинном временно́м окне — форшоки
           (также помечаются зависимыми).

        Args:
            df: DataFrame с колонками ``time`` (datetime) или ``year/month/day``,
                ``lat``/``latitude``, ``lon``/``longitude``, ``magnitude``.

        Returns:
            Кортеж ``(mainshocks_df, aftershocks_df)``.
        """
        df = df.copy().reset_index(drop=True)
        lat_col, lon_col = _get_lat_lon_cols(df)

        times_days = _to_time_days(df)
        lats = df[lat_col].values.astype(float)
        lons = df[lon_col].values.astype(float)
        mags = df["magnitude"].fillna(5.0).values.astype(float)

        n = len(df)
        is_dependent = np.zeros(n, dtype=bool)

        # Обрабатываем в порядке убывания магнитуды
        order = np.argsort(-mags)

        for idx in order:
            if is_dependent[idx]:
                continue

            m = mags[idx]
            t0 = times_days[idx]
            t_win, r_win = self._get_window(m)

            for j in range(n):
                if j == idx or is_dependent[j]:
                    continue
                dt = times_days[j] - t0
                # Афтершоки: [0, t_win], форшоки: [-t_win/2, 0)
                if -t_win / 2.0 <= dt <= t_win:
                    dist = _haversine_km(lats[idx], lons[idx], lats[j], lons[j])
                    if dist <= r_win and dt != 0:
                        is_dependent[j] = True

        mainshocks = df[~is_dependent].copy()
        aftershocks = df[is_dependent].copy()

        logger.info(
            "Gardner-Knopoff: %d главных толчков, %d афтершоков/форшоков",
            len(mainshocks), len(aftershocks),
        )
        return mainshocks, aftershocks


# ---------------------------------------------------------------------------
# Zaliapin & Ben-Zion (2013)
# ---------------------------------------------------------------------------

class ZaliaipinDeclustering:
    """Декластеризация методом ближайшего соседа (Zaliapin & Ben-Zion, 2013).

    Метрика расстояния между событиями j и i (i предшествует j):

        η_ij = t_ij^1 * r_ij^df * 10^(-b*m_i/2)

    где t в годах, r в км. Для каждого события j выбирается «родитель» i
    с минимальным η_ij. Распределение log₁₀(η) бимодально: фоновые
    события формируют правый моду, связанные — левый. Разрез по минимуму
    плотности между модами даёт порог η₀.
    """

    def __init__(
        self,
        df_param: float = 1.6,
        b_param: float = 1.0,
    ) -> None:
        """
        Args:
            df_param: фрактальная размерность (обычно 1.6).
            b_param: b-value закона Гутенберга-Рихтера.
        """
        self.df_param = df_param
        self.b_param = b_param

    def _compute_eta(
        self,
        times_years: np.ndarray,
        lats: np.ndarray,
        lons: np.ndarray,
        mags: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Вычисляет η для каждого события и индекс его «родителя».

        Returns:
            Кортеж ``(eta_array, parent_idx_array)``.
            Для первого события eta=inf, parent=-1.
        """
        n = len(times_years)
        etas = np.full(n, np.inf)
        parents = np.full(n, -1, dtype=int)

        for j in range(1, n):
            best = np.inf
            best_i = -1
            for i in range(j):
                dt = times_years[j] - times_years[i]
                if dt <= 0:
                    continue
                dr = _haversine_km(lats[i], lons[i], lats[j], lons[j])
                if dr <= 0:
                    dr = 0.1
                eta = dt * (dr ** self.df_param) * (10 ** (-self.b_param * mags[i] / 2))
                if eta < best:
                    best = eta
                    best_i = i
            etas[j] = best
            parents[j] = best_i

        return etas, parents

    def find_threshold_kde(self, eta_values: np.ndarray) -> float:
        """Находит порог η₀ между двумя модами log(η) через KDE.

        Алгоритм:
        1. KDE на log10(eta_values) с узкой полосой (bw=0.15).
        2. Найти все локальные минимумы на сетке из 500 точек.
        3. Выбрать минимум между двумя наибольшими пиками KDE.

        Args:
            eta_values: массив значений η (положительные).

        Returns:
            Порог η₀ в исходном масштабе (не log).
        """
        from scipy.stats import gaussian_kde as _gkde
        from scipy.signal import argrelmin

        valid = eta_values[np.isfinite(eta_values) & (eta_values > 0)]
        if len(valid) < 10:
            return float(np.median(valid)) if len(valid) > 0 else 1e-5

        log_eta = np.log10(valid)
        x = np.linspace(log_eta.min(), log_eta.max(), 500)
        kde = _gkde(log_eta, bw_method=0.15)
        density = kde(x)

        # Находим локальные минимумы
        mins_idx = argrelmin(density, order=10)[0]
        if len(mins_idx) == 0:
            return float(10 ** np.median(log_eta))

        # Находим два наибольших пика
        peaks_idx = np.argsort(density)[::-1]
        # Выбираем минимум между двумя крупнейшими пиками
        if len(peaks_idx) >= 2:
            p1, p2 = sorted([peaks_idx[0], peaks_idx[1]])
            # Все минимумы между p1 и p2
            between = mins_idx[(mins_idx > p1) & (mins_idx < p2)]
            if len(between) > 0:
                # Минимум с наименьшей плотностью между двумя пиками
                best_min = between[np.argmin(density[between])]
                return float(10 ** x[best_min])

        # Фолбэк: минимум ближайший к медиане
        med_idx = int(np.searchsorted(x, np.median(log_eta)))
        closest = mins_idx[np.argmin(np.abs(mins_idx - med_idx))]
        return float(10 ** x[closest])

    def plot_eta_distribution(
        self,
        eta_values: np.ndarray,
        threshold: float,
        output_path: str | None = None,
    ) -> None:
        """Визуализация бимодального распределения log₁₀(η) с порогом.

        Строит гистограмму + KDE с вертикальной линией порога.
        Требует matplotlib.

        Args:
            eta_values: массив значений η.
            threshold: порог η₀ в исходном масштабе.
            output_path: путь для сохранения PNG. Если None — отображается.
        """
        try:
            import matplotlib.pyplot as plt
            from scipy.stats import gaussian_kde as _gkde
        except ImportError:
            logger.warning("matplotlib/scipy не установлен, plot пропущен.")
            return

        valid = eta_values[np.isfinite(eta_values) & (eta_values > 0)]
        log_eta = np.log10(valid)
        log_thresh = np.log10(threshold)

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.hist(log_eta, bins=80, density=True, alpha=0.4, color="steelblue",
                label="log₁₀(η) гистограмма")

        x_grid = np.linspace(log_eta.min(), log_eta.max(), 500)
        kde = _gkde(log_eta, bw_method=0.15)
        ax.plot(x_grid, kde(x_grid), "b-", lw=2, label="KDE")

        ax.axvline(log_thresh, color="red", lw=2, ls="--",
                   label=f"η₀ = {threshold:.2e} (log={log_thresh:.2f})")

        n_bg = int(np.sum(np.log10(valid) > log_thresh))
        n_cl = int(np.sum(np.log10(valid) <= log_thresh))
        ax.set_xlabel("log₁₀(η)")
        ax.set_ylabel("Плотность")
        ax.set_title(
            f"Распределение метрики Залиапина–Бен-Зиона\n"
            f"Фоновые: {n_bg}  |  Кластерные: {n_cl}  |  Всего: {len(valid)}"
        )
        ax.legend()
        fig.tight_layout()

        if output_path:
            fig.savefig(output_path, dpi=150)
            logger.info("График сохранён: %s", output_path)
        else:
            plt.show()
        plt.close(fig)

    @staticmethod
    def _find_eta0_from_bimodal(log_etas: np.ndarray) -> float:
        """Определяет порог η₀ по минимуму KDE между двумя модами.

        Args:
            log_etas: массив log₁₀(η) для всех связанных событий.

        Returns:
            Значение log₁₀(η₀) — оптимальный порог разреза.
        """
        finite = log_etas[np.isfinite(log_etas)]
        if len(finite) < 10:
            return float(np.median(finite)) if len(finite) > 0 else -5.0

        kde = gaussian_kde(finite, bw_method="silverman")
        x_grid = np.linspace(finite.min(), finite.max(), 500)
        density = kde(x_grid)

        # Ищем минимум между двумя пиками (середина диапазона как начальная точка)
        mid = len(x_grid) // 2
        # Находим локальные минимумы
        from scipy.signal import argrelmin
        local_mins = argrelmin(density, order=10)[0]

        if len(local_mins) > 0:
            # Берём ближайший к медиане минимум
            med_idx = np.searchsorted(x_grid, np.median(finite))
            closest = local_mins[np.argmin(np.abs(local_mins - med_idx))]
            return float(x_grid[closest])

        return float(np.median(finite))

    def decluster(
        self,
        df: pd.DataFrame,
        eta_0: float | None = None,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Разделяет каталог на фоновые события и связанные.

        Args:
            df: DataFrame с колонками ``time`` (datetime) или ``year/month/day``,
                ``lat``/``latitude``, ``lon``/``longitude``, ``magnitude``.
            eta_0: порог η₀ в пространстве η (не log). Если ``None``,
                   определяется автоматически по бимодальному распределению log(η).

        Returns:
            Кортеж ``(background_df, clustered_df)``.
        """
        df = df.copy().reset_index(drop=True)
        lat_col, lon_col = _get_lat_lon_cols(df)

        # Время в годах
        t_days = _to_time_days(df)
        times_years = t_days / 365.25

        lats = df[lat_col].values.astype(float)
        lons = df[lon_col].values.astype(float)
        mags = df["magnitude"].fillna(6.0).values.astype(float)

        etas, parents = self._compute_eta(times_years, lats, lons, mags)

        # Автоматический выбор порога
        if eta_0 is None:
            valid = etas[np.isfinite(etas) & (etas > 0)]
            log_etas = np.log10(valid) if len(valid) > 0 else np.array([-5.0])
            log_eta0 = self._find_eta0_from_bimodal(log_etas)
            eta_0 = float(10 ** log_eta0)
            logger.info("Автоматический порог η₀ = %.4e (log₁₀ = %.2f)", eta_0, log_eta0)

        is_clustered = (etas < eta_0) & (parents >= 0)

        df["eta_zb"] = etas
        df["parent_zb"] = parents

        background = df[~is_clustered].drop(columns=["eta_zb", "parent_zb"])
        clustered = df[is_clustered].drop(columns=["eta_zb", "parent_zb"])

        logger.info(
            "Zaliapin-BZ: %d фоновых событий, %d связанных (η₀=%.4e)",
            len(background), len(clustered), eta_0,
        )
        return background, clustered


# ---------------------------------------------------------------------------
# Сравнение методов
# ---------------------------------------------------------------------------

def compare_declustering_methods(df: pd.DataFrame) -> pd.DataFrame:
    """Запускает оба метода декластеризации и возвращает сравнительную таблицу.

    Args:
        df: DataFrame с полями ``time``/``year``/``month``/``day``,
            ``lat``/``latitude``, ``lon``/``longitude``, ``magnitude``.

    Returns:
        DataFrame с колонками:
        ``n_total``, ``n_mainshocks_gk``, ``n_mainshocks_zb``,
        ``n_aftershocks_gk``, ``n_aftershocks_zb``,
        ``reduction_gk_pct``, ``reduction_zb_pct``.
    """
    n_total = len(df)

    gk = GardnerKnopoffDeclustering()
    main_gk, after_gk = gk.decluster(df)

    zb = ZaliaipinDeclustering()
    back_zb, clust_zb = zb.decluster(df)

    n_main_gk = len(main_gk)
    n_after_gk = len(after_gk)
    n_main_zb = len(back_zb)
    n_after_zb = len(clust_zb)

    reduction_gk = 100.0 * n_after_gk / n_total if n_total > 0 else 0.0
    reduction_zb = 100.0 * n_after_zb / n_total if n_total > 0 else 0.0

    return pd.DataFrame(
        [{
            "n_total": n_total,
            "n_mainshocks_gk": n_main_gk,
            "n_mainshocks_zb": n_main_zb,
            "n_aftershocks_gk": n_after_gk,
            "n_aftershocks_zb": n_after_zb,
            "reduction_gk_pct": round(reduction_gk, 2),
            "reduction_zb_pct": round(reduction_zb, 2),
        }]
    )
