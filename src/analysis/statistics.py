"""Статистические функции для анализа сейсмических серий."""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import lognorm, expon, kstest

logger = logging.getLogger(__name__)


def interevent_distribution(
    series_df: pd.DataFrame,
) -> dict[str, Any]:
    """Вычисляет распределение интервалов между событиями серии.

    Аппроксимирует логнормальным и экспоненциальным законами.
    Поддерживает как datetime-колонку time, так и year/month/day.

    Args:
        series_df: DataFrame одной серии.

    Returns:
        Словарь с ключами mean_days, std_days, lognormal_params, ks_pvalue
        и дополнительно intervals_days, lognorm, expon.
    """
    _nan = float("nan")
    _empty: dict[str, Any] = {
        "mean_days": _nan,
        "std_days": _nan,
        "lognormal_params": (_nan, _nan),
        "ks_pvalue": _nan,
        "intervals_days": np.array([]),
        "lognorm": None,
        "expon": None,
    }

    if "time" in series_df.columns:
        times_dt = pd.to_datetime(series_df["time"]).sort_values().reset_index(drop=True)
        if len(times_dt) < 2:
            return _empty
        intervals = (
            np.diff(times_dt.values).astype("timedelta64[s]").astype(float) / 86400.0
        )
    else:
        from .clustering import _events_to_time_years
        raw_times = np.sort(_events_to_time_years(series_df))
        if len(raw_times) < 2:
            return _empty
        intervals = np.diff(raw_times) * 365.25

    intervals = intervals[intervals > 0]
    if len(intervals) == 0:
        return _empty

    mean_days = float(np.mean(intervals))
    std_days = float(np.std(intervals, ddof=1)) if len(intervals) > 1 else _nan

    result: dict[str, Any] = {
        "mean_days": mean_days,
        "std_days": std_days,
        "lognormal_params": (_nan, _nan),
        "ks_pvalue": _nan,
        "intervals_days": intervals,
        "lognorm": None,
        "expon": None,
    }

    # Аппроксимация логнормальным
    if len(intervals) >= 3 and np.all(intervals > 0):
        try:
            s, loc, scale = lognorm.fit(intervals, floc=0)
            ks_stat, ks_p = kstest(intervals, "lognorm", args=(s, loc, scale))
            mu_ln = float(np.log(scale))
            sigma_ln = float(s)
            result["lognormal_params"] = (mu_ln, sigma_ln)
            result["ks_pvalue"] = float(ks_p)
            result["lognorm"] = {
                "s": s, "loc": loc, "scale": scale,
                "ks_stat": float(ks_stat), "ks_p": float(ks_p),
                "mean_days": mean_days,
                "median_days": float(lognorm.median(s, loc, scale)),
            }
        except Exception as exc:
            logger.debug("Логнормальная аппроксимация не удалась: %s", exc)

    # Аппроксимация экспоненциальным
    if len(intervals) >= 3:
        try:
            loc_e, scale_e = expon.fit(intervals, floc=0)
            ks_stat_e, ks_p_e = kstest(intervals, "expon", args=(loc_e, scale_e))
            result["expon"] = {
                "loc": loc_e, "scale": scale_e,
                "ks_stat": float(ks_stat_e), "ks_p": float(ks_p_e),
                "mean_days": float(scale_e),
            }
        except Exception as exc:
            logger.debug("Экспоненциальная аппроксимация не удалась: %s", exc)

    return result


def spatial_extent(series_df: pd.DataFrame) -> float:
    """Вычисляет площадь выпуклой оболочки серии в кв. градусах.

    Args:
        series_df: DataFrame с колонками lat, lon.

    Returns:
        Площадь выпуклой оболочки в кв. градусах (0 если < 3 точек).
    """
    coords = series_df[["lat", "lon"]].dropna().values
    if len(coords) < 3:
        return 0.0

    try:
        from scipy.spatial import ConvexHull
        hull = ConvexHull(coords)
        return float(hull.volume)  # для 2D hull.volume = площадь
    except Exception as exc:
        logger.debug("Convex hull не удался: %s", exc)
        # Фолбэк: площадь bounding box
        lat_range = float(np.ptp(coords[:, 0]))
        lon_range = float(np.ptp(coords[:, 1]))
        return lat_range * lon_range


def magnitude_energy_release(series_df: pd.DataFrame) -> float:
    """Вычисляет суммарный сейсмический момент серии.

    Момент Mo = 10^(1.5 * M + 9.1) в Нм (формула Hanks & Kanamori, 1979).

    Args:
        series_df: DataFrame с колонкой magnitude.

    Returns:
        Суммарный сейсмический момент в Нм.
    """
    mags = series_df["magnitude"].dropna().values
    if len(mags) == 0:
        return 0.0

    moments = 10 ** (1.5 * mags + 9.1)
    total_moment = float(np.sum(moments))
    mw_equiv = (np.log10(total_moment) - 9.1) / 1.5
    logger.debug(
        "Суммарный момент серии: %.2e Нм (Mw_equiv=%.1f)",
        total_moment, mw_equiv,
    )
    return total_moment


def series_summary_table(all_series: list[pd.DataFrame]) -> pd.DataFrame:
    """Строит сводную таблицу всех идентифицированных серий.

    Поддерживает оба формата данных:
    - time/latitude/longitude/magnitude (datetime-формат)
    - year/month/day/lat/lon/magnitude (числовой формат)

    Args:
        all_series: список DataFrame, каждый — одна глобальная серия.

    Returns:
        DataFrame с колонками: series_id, n_events, duration_days,
        n_regions, max_magnitude, spatial_extent_km2, total_moment_Nm, pvalue.
    """
    _columns = [
        "series_id", "n_events", "year_start", "year_end", "duration_days",
        "n_regions", "max_magnitude", "spatial_extent_km2", "total_moment_Nm", "pvalue",
    ]

    if not all_series:
        return pd.DataFrame(columns=_columns)

    rows = []
    for idx, series in enumerate(all_series):
        if series.empty:
            continue

        mags = series["magnitude"].dropna().values

        # Длительность в днях
        if "time" in series.columns:
            times_dt = pd.to_datetime(series["time"])
            duration_days = (
                (times_dt.max() - times_dt.min()).total_seconds() / 86400.0
            )
        else:
            from .clustering import _events_to_time_years
            times = np.sort(_events_to_time_years(series))
            duration_days = float(np.ptp(times)) * 365.25 if len(times) > 1 else 0.0

        # Число регионов
        for rcol in ("fe_region", "region"):
            if rcol in series.columns:
                n_regions = int(series[rcol].nunique())
                break
        else:
            n_regions = 0

        # p-value из данных (если есть)
        pvalue = float("nan")
        if "pvalue" in series.columns:
            pv = series["pvalue"].dropna()
            if not pv.empty:
                pvalue = float(pv.iloc[0])

        # year_start / year_end — из колонки year или из time
        year_start: int | None = None
        year_end: int | None = None
        if "year" in series.columns:
            yr = series["year"].dropna()
            if not yr.empty:
                year_start = int(yr.min())
                year_end = int(yr.max())
        elif "time" in series.columns:
            times_dt2 = pd.to_datetime(series["time"])
            year_start = int(times_dt2.min().year)
            year_end = int(times_dt2.max().year)

        row: dict[str, Any] = {
            "series_id": idx,
            "n_events": len(series),
            "year_start": year_start,
            "year_end": year_end,
            "duration_days": round(duration_days, 2),
            "n_regions": n_regions,
            "max_magnitude": float(np.max(mags)) if len(mags) > 0 else float("nan"),
            "spatial_extent_km2": round(spatial_extent_km2(series), 2),
            "total_moment_Nm": magnitude_energy_release(series),
            "pvalue": pvalue,
        }
        rows.append(row)

    if not rows:
        return pd.DataFrame(columns=_columns)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Compatibility aliases and additional functions for test interface
# ---------------------------------------------------------------------------

def seismic_moment_sum(series_df: pd.DataFrame) -> float:
    """Суммарный сейсмический момент серии в Н·м.

    Псевдоним для magnitude_energy_release.
    """
    return magnitude_energy_release(series_df)


def spatial_extent_km2(series_df: pd.DataFrame) -> float:
    """Площадь convex hull событий серии в км².

    Проецирует координаты в км через равнопромежуточную проекцию
    относительно центроида и вычисляет площадь выпуклой оболочки.

    Args:
        series_df: DataFrame с колонками latitude/longitude или lat/lon.

    Returns:
        Площадь в км². Если событий < 3 или hull вырожден, возвращает 0.0.
    """
    lat_col = "latitude" if "latitude" in series_df.columns else "lat"
    lon_col = "longitude" if "longitude" in series_df.columns else "lon"

    lats = series_df[lat_col].dropna().values
    lons = series_df[lon_col].dropna().values

    if len(lats) < 3:
        return 0.0

    lat0 = float(np.mean(lats))
    lon0 = float(np.mean(lons))
    r_km = 6371.0

    x = r_km * np.radians(lons - lon0) * np.cos(np.radians(lat0))
    y = r_km * np.radians(lats - lat0)

    points = np.column_stack([x, y])
    unique_points = np.unique(points, axis=0)
    if unique_points.shape[0] < 3:
        return 0.0

    try:
        from scipy.spatial import ConvexHull
        hull = ConvexHull(unique_points)
        return float(hull.volume)
    except Exception:
        return 0.0
