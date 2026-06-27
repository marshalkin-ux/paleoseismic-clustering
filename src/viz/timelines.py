"""Временны́е диаграммы сейсмических серий и плотности событий."""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde

from .style import (
    DPI,
    FIGURE_SIZE_TIMELINE,
    PALETTE_SERIES,
    apply_style,
    magnitude_to_markersize,
)

logger = logging.getLogger(__name__)


def plot_series_timeline(
    series: pd.DataFrame,
    output_path: str | Path,
    series_id: int = 0,
    title: str | None = None,
) -> None:
    """Горизонтальная временна́я шкала одной сейсмической серии.

    Каждое событие обозначается маркером, размер которого пропорционален
    магнитуде. Цвет кодирует глубину очага.

    Args:
        series: DataFrame одной серии.
        output_path: путь для сохранения PNG.
        series_id: номер серии для цвета.
        title: заголовок; если None — генерируется автоматически.
    """
    apply_style()
    from ..analysis.clustering import _events_to_time_years

    times = _events_to_time_years(series)
    mags = series["magnitude"].fillna(6.5).values
    depths = series["depth_km"].fillna(30).values
    event_ids = series.get("event_id", pd.Series(range(len(series)))).values

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_TIMELINE)

    scatter = ax.scatter(
        times,
        np.ones(len(times)),
        s=[magnitude_to_markersize(m) for m in mags],
        c=depths,
        cmap="plasma",
        alpha=0.8,
        edgecolors="white",
        linewidths=0.5,
        zorder=3,
    )

    # Вертикальные линии для каждого события
    for t in times:
        ax.axvline(t, color="gray", linewidth=0.3, alpha=0.5, zorder=1)

    plt.colorbar(scatter, ax=ax, label="Глубина (км)", shrink=0.6, pad=0.01)

    ax.set_yticks([])
    ax.set_xlabel("Год")
    ax.set_xlim(times.min() - 0.5, times.max() + 0.5)

    if title is None:
        year_start = int(series["year"].min()) if len(series) > 0 else "?"
        year_end = int(series["year"].max()) if len(series) > 0 else "?"
        n_reg = series["fe_region"].nunique() if "fe_region" in series.columns else "?"
        title = f"Серия #{series_id + 1}: {year_start}–{year_end}, n={len(series)}, регионов={n_reg}"

    ax.set_title(title, fontsize=12)
    plt.tight_layout()
    plt.savefig(str(output_path), dpi=DPI, bbox_inches="tight")
    plt.close()
    logger.info("Временна́я шкала серии сохранена: %s", output_path)


def plot_event_density(
    df: pd.DataFrame,
    output_path: str | Path,
    bandwidth_years: float = 5.0,
    highlight_clusters: bool = True,
    title: str = "Плотность глобальных событий M≥6.5",
) -> None:
    """Временной ряд плотности событий с KDE.

    Args:
        df: DataFrame с колонками year, magnitude, cluster_id.
        output_path: путь для сохранения PNG.
        bandwidth_years: ширина ядра KDE в годах.
        highlight_clusters: выделить ли кластеризованные события.
        title: заголовок.
    """
    apply_style()
    from ..analysis.clustering import _events_to_time_years

    times = _events_to_time_years(df)
    t_grid = np.linspace(times.min(), times.max(), 1000)

    # KDE плотности
    bw = bandwidth_years / (times.max() - times.min())
    try:
        kde = gaussian_kde(times, bw_method=bw)
        density = kde(t_grid)
    except Exception:
        density = np.zeros_like(t_grid)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(FIGURE_SIZE_TIMELINE[0], 8),
                                    sharex=True)

    # Верхняя панель: KDE
    ax1.fill_between(t_grid, density, alpha=0.4, color="#1f77b4")
    ax1.plot(t_grid, density, color="#1f77b4", linewidth=1.5)
    ax1.set_ylabel("Плотность событий (KDE)")
    ax1.set_title(title)

    # Нижняя панель: временной ряд кумулятивного числа
    ax2.plot(sorted(times), np.arange(1, len(times) + 1),
             color="#ff7f0e", linewidth=1.5, label="Кумулятивное число")
    ax2.set_xlabel("Год")
    ax2.set_ylabel("Кумулятивное число событий")

    # Выделение кластеров
    if highlight_clusters and "cluster_id" in df.columns:
        clustered = df[df["cluster_id"] >= 0]
        ct = _events_to_time_years(clustered)
        ax2.scatter(ct, np.searchsorted(sorted(times), ct),
                    c="red", s=15, alpha=0.6, zorder=5, label="Кластеры")
        ax2.legend(fontsize=9)

    plt.tight_layout()
    plt.savefig(str(output_path), dpi=DPI, bbox_inches="tight")
    plt.close()
    logger.info("График плотности сохранён: %s", output_path)


def plot_interevent_histogram(
    series_df: pd.DataFrame,
    output_path: str | Path,
    title: str = "Распределение интервалов между событиями",
) -> None:
    """Гистограмма интервалов внутри серии + логнормальная аппроксимация.

    Args:
        series_df: DataFrame одной серии.
        output_path: путь для сохранения PNG.
        title: заголовок.
    """
    apply_style()
    from ..analysis.statistics import interevent_distribution

    istat = interevent_distribution(series_df)
    intervals = istat.get("intervals_days", np.array([]))

    if len(intervals) < 2:
        logger.warning("Недостаточно интервалов для гистограммы")
        return

    fig, ax = plt.subplots(figsize=FIGURE_SIZE_TIMELINE)

    # Гистограмма
    counts, bin_edges, patches = ax.hist(
        intervals,
        bins=min(20, max(5, len(intervals) // 2)),
        density=True,
        color="#1f77b4",
        alpha=0.6,
        edgecolor="white",
        label="Наблюдаемые интервалы",
    )

    # Аппроксимации
    x = np.linspace(0, np.max(intervals) * 1.2, 200)

    lnorm = istat.get("lognorm")
    if lnorm:
        from scipy.stats import lognorm
        y_ln = lognorm.pdf(x, lnorm["s"], lnorm["loc"], lnorm["scale"])
        ax.plot(
            x, y_ln,
            color="#d62728", linewidth=2, linestyle="-",
            label=f"Логнормальное (σ={lnorm['s']:.2f}, p={lnorm['ks_p']:.3f})",
        )

    exp_fit = istat.get("expon")
    if exp_fit:
        from scipy.stats import expon
        y_ex = expon.pdf(x, exp_fit["loc"], exp_fit["scale"])
        ax.plot(
            x, y_ex,
            color="#2ca02c", linewidth=2, linestyle="--",
            label=f"Экспоненциальное (λ={1/exp_fit['scale']:.4f} д⁻¹, p={exp_fit['ks_p']:.3f})",
        )

    ax.set_xlabel("Интервал (дни)")
    ax.set_ylabel("Плотность вероятности")
    ax.set_title(title)
    ax.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig(str(output_path), dpi=DPI, bbox_inches="tight")
    plt.close()
    logger.info("Гистограмма интервалов сохранена: %s", output_path)
