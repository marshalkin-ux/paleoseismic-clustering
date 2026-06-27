"""Глобальные карты сейсмических серий и плотности событий.

Использует Cartopy (проекция Robinson) для визуализации.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .style import (
    DPI,
    FIGURE_SIZE_MAP,
    PALETTE_SERIES,
    apply_style,
    magnitude_to_markersize,
)

logger = logging.getLogger(__name__)


def plot_global_series_map(
    series_list: list[pd.DataFrame],
    output_path: str | Path,
    title: str = "Глобальные сейсмические серии",
) -> None:
    """Строит глобальную карту всех идентифицированных серий.

    Каждая серия отображается своим цветом. Размер маркера
    пропорционален магнитуде события.

    Args:
        series_list: список DataFrame (каждый — одна серия).
        output_path: путь для сохранения PNG-файла.
        title: заголовок карты.
    """
    apply_style()

    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature

        fig = plt.figure(figsize=FIGURE_SIZE_MAP)
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson())
        ax.set_global()

        # Подложка карты
        ax.add_feature(cfeature.LAND, facecolor="#f0efe7", edgecolor="#888888", linewidth=0.3)
        ax.add_feature(cfeature.OCEAN, facecolor="#cce5f0")
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor="#666666")
        ax.add_feature(cfeature.BORDERS, linewidth=0.3, edgecolor="#aaaaaa")
        ax.gridlines(linewidth=0.3, color="gray", alpha=0.5, linestyle="--")

        for idx, series in enumerate(series_list):
            color = PALETTE_SERIES[idx % len(PALETTE_SERIES)]
            for _, row in series.iterrows():
                if pd.isna(row.get("lat")) or pd.isna(row.get("lon")):
                    continue
                mag = row.get("magnitude", 6.5)
                size = magnitude_to_markersize(float(mag) if pd.notna(mag) else 6.5)
                ax.scatter(
                    row["lon"], row["lat"],
                    s=size,
                    c=color,
                    alpha=0.75,
                    transform=ccrs.PlateCarree(),
                    zorder=5,
                    edgecolors="white",
                    linewidths=0.3,
                )

        # Легенда для магнитуд
        legend_mags = [6.5, 7.0, 7.5, 8.0]
        legend_handles = [
            plt.scatter([], [], s=magnitude_to_markersize(m), c="gray", alpha=0.7,
                        edgecolors="white", linewidths=0.3, label=f"M {m:.1f}")
            for m in legend_mags
        ]
        ax.legend(
            handles=legend_handles,
            title="Магнитуда",
            loc="lower left",
            framealpha=0.9,
            fontsize=9,
        )

        ax.set_title(title, fontsize=14, pad=12)
        plt.tight_layout()
        plt.savefig(str(output_path), dpi=DPI, bbox_inches="tight")
        plt.close()
        logger.info("Карта серий сохранена: %s", output_path)

    except ImportError:
        logger.warning("Cartopy недоступна, используем упрощённую карту matplotlib")
        _plot_fallback_map(series_list, output_path, title)


def _plot_fallback_map(
    series_list: list[pd.DataFrame],
    output_path: str | Path,
    title: str,
) -> None:
    """Упрощённая карта без Cartopy."""
    fig, ax = plt.subplots(figsize=FIGURE_SIZE_MAP)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_xlabel("Долгота")
    ax.set_ylabel("Широта")
    ax.set_title(title)

    for idx, series in enumerate(series_list):
        color = PALETTE_SERIES[idx % len(PALETTE_SERIES)]
        valid = series.dropna(subset=["lat", "lon", "magnitude"])
        sizes = [magnitude_to_markersize(m) for m in valid["magnitude"].values]
        ax.scatter(
            valid["lon"].values, valid["lat"].values,
            s=sizes, c=color, alpha=0.7, edgecolors="white", linewidths=0.3,
            label=f"Серия {idx + 1}",
        )

    ax.legend(loc="lower left", fontsize=8, ncol=2)
    plt.tight_layout()
    plt.savefig(str(output_path), dpi=DPI, bbox_inches="tight")
    plt.close()


def plot_density_map(
    df: pd.DataFrame,
    output_path: str | Path,
    grid_size: int = 90,
    title: str = "Плотность событий M>=6.5",
) -> None:
    """Строит тепловую карту плотности событий.

    Args:
        df: DataFrame с колонками lat, lon, magnitude.
        output_path: путь для сохранения PNG.
        grid_size: разрешение сетки (градусов).
        title: заголовок карты.
    """
    apply_style()

    valid = df.dropna(subset=["lat", "lon"])
    lats = valid["lat"].values
    lons = valid["lon"].values

    # Двумерная гистограмма
    lon_bins = np.linspace(-180, 180, grid_size + 1)
    lat_bins = np.linspace(-90, 90, grid_size // 2 + 1)
    density, _, _ = np.histogram2d(lons, lats, bins=[lon_bins, lat_bins])
    density = density.T  # (lat, lon)

    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
        from matplotlib.colors import LogNorm

        fig = plt.figure(figsize=FIGURE_SIZE_MAP)
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson())
        ax.set_global()

        ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor="#333333")
        ax.add_feature(cfeature.BORDERS, linewidth=0.3, edgecolor="#aaaaaa")
        ax.gridlines(linewidth=0.3, color="gray", alpha=0.4)

        lon_centers = (lon_bins[:-1] + lon_bins[1:]) / 2
        lat_centers = (lat_bins[:-1] + lat_bins[1:]) / 2
        LON, LAT = np.meshgrid(lon_centers, lat_centers)

        density_masked = np.ma.masked_where(density == 0, density)
        norm = LogNorm(vmin=1, vmax=max(density.max(), 2))
        im = ax.pcolormesh(
            LON, LAT, density_masked,
            cmap="viridis", norm=norm,
            transform=ccrs.PlateCarree(),
            alpha=0.85,
        )

        plt.colorbar(im, ax=ax, orientation="horizontal", pad=0.02,
                     label="Число событий в ячейке", shrink=0.6)
        ax.set_title(title, fontsize=14, pad=12)

    except ImportError:
        fig, ax = plt.subplots(figsize=FIGURE_SIZE_MAP)
        from matplotlib.colors import LogNorm
        density_masked = np.ma.masked_where(density == 0, density)
        im = ax.pcolormesh(
            np.linspace(-180, 180, grid_size),
            np.linspace(-90, 90, grid_size // 2),
            density_masked, cmap="viridis",
            norm=LogNorm(vmin=1, vmax=max(density.max(), 2)),
        )
        plt.colorbar(im, ax=ax, label="Число событий")
        ax.set_xlabel("Долгота")
        ax.set_ylabel("Широта")
        ax.set_title(title)

    plt.tight_layout()
    plt.savefig(str(output_path), dpi=DPI, bbox_inches="tight")
    plt.close()
    logger.info("Карта плотности сохранена: %s", output_path)
