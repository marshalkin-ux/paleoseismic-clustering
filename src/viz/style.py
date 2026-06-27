"""Единый стиль визуализации проекта paleoseismic-clustering."""

from __future__ import annotations

import matplotlib.pyplot as plt

# Цветовая палитра для серий (tab10)
PALETTE_SERIES = [
    "#1f77b4",  # синий
    "#ff7f0e",  # оранжевый
    "#2ca02c",  # зелёный
    "#d62728",  # красный
    "#9467bd",  # фиолетовый
    "#8c564b",  # коричневый
    "#e377c2",  # розовый
    "#7f7f7f",  # серый
    "#bcbd22",  # жёлто-зелёный
    "#17becf",  # голубой
]

PALETTE_DENSITY = "viridis"
FONT_FAMILY = "DejaVu Sans"
DPI = 300
FIGURE_SIZE_MAP = (16, 9)
FIGURE_SIZE_TIMELINE = (14, 6)

# Размер маркера пропорционален магнитуде: marker_size = BASE_MARKER * 1.5^(M-6)
BASE_MARKER = 20


def apply_style() -> None:
    """Применяет единый стиль matplotlib ко всем последующим графикам."""
    plt.rcParams.update({
        "font.family": FONT_FAMILY,
        "font.size": 11,
        "axes.titlesize": 13,
        "axes.labelsize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.dpi": 100,
        "savefig.dpi": DPI,
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def magnitude_to_markersize(magnitude: float, base: float = BASE_MARKER) -> float:
    """Масштабирует размер маркера пропорционально магнитуде.

    Args:
        magnitude: магнитуда землетрясения.
        base: базовый размер для M=6.

    Returns:
        Размер маркера в пикселях.
    """
    return base * (1.5 ** max(0, magnitude - 6.0))
