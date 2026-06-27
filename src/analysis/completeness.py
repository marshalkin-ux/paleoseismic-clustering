"""Анализ полноты каталога землетрясений.

Реализует оценку магнитуды полноты Mc методом максимальной кривизны
и вычисление b-value по методу максимального правдоподобия.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd
logger = logging.getLogger(__name__)


class CompletenessAnalyzer:
    """Анализатор полноты сейсмического каталога.

    Пример::

        analyzer = CompletenessAnalyzer()
        mc = analyzer.estimate_mc(df, region=1, period_start=1990, period_end=2020)
        b, db = analyzer.compute_bvalue(df, mc)
    """

    def estimate_mc(
        self,
        df: pd.DataFrame,
        region: int | None = None,
        period_start: int | None = None,
        period_end: int | None = None,
    ) -> float:
        """Оценивает магнитуду полноты Mc методом максимальной кривизны.

        Максимальная кривизна — точка, где производная частотно-магнитудного
        распределения максимальна (Woessner & Wiemer, 2005).

        Args:
            df: DataFrame с колонкой magnitude.
            region: код региона Flinn-Engdahl (None = все).
            period_start: начальный год периода.
            period_end: конечный год периода.

        Returns:
            Оценка Mc.
        """
        sub = self._filter(df, region, period_start, period_end)
        mags = sub["magnitude"].dropna().values

        if len(mags) < 20:
            logger.warning("Слишком мало событий (%d) для оценки Mc", len(mags))
            return float(np.min(mags)) if len(mags) > 0 else 0.0

        bin_size = 0.1
        mag_min = np.floor(np.min(mags) * 10) / 10
        mag_max = np.ceil(np.max(mags) * 10) / 10
        bins = np.arange(mag_min, mag_max + bin_size, bin_size)

        counts, edges = np.histogram(mags, bins=bins)
        centers = (edges[:-1] + edges[1:]) / 2

        # Индекс максимума дифференциального распределения частот
        mc_idx = int(np.argmax(counts))
        mc = float(centers[mc_idx])

        logger.debug(
            "Mc оценена: %.2f (регион=%s, %s-%s, n=%d)",
            mc, region, period_start, period_end, len(mags),
        )
        return mc

    def compute_bvalue(
        self,
        df: pd.DataFrame,
        mc: float,
        magnitude_col: str = "magnitude",
    ) -> tuple[float, float]:
        """Вычисляет b-value методом максимального правдоподобия.

        Формула Aki (1965), погрешность по Shi & Bolt (1982)::

            b = log10(e) / (mean(M) - Mc)
            sigma_b = 2.3 * b^2 * std(M) / sqrt(n)

        Args:
            df: DataFrame с магнитудами.
            mc: магнитуда полноты.
            magnitude_col: имя колонки с магнитудами.

        Returns:
            Кортеж (b_value, sigma_b).
        """
        mags = df[magnitude_col].dropna().values
        mags = mags[mags >= mc]

        if len(mags) < 10:
            logger.warning("Недостаточно событий выше Mc=%.2f", mc)
            return (1.0, 0.1)

        mean_m = np.mean(mags)
        std_m = np.std(mags, ddof=1)
        n = len(mags)

        # Оценка Aki (максимальное правдоподобие)
        b = np.log10(np.e) / (mean_m - mc + 0.05)  # +0.05 — коррекция на дискретность
        sigma_b = 2.3 * (b ** 2) * std_m / np.sqrt(n)

        logger.info("b-value = %.3f ± %.3f (n=%d, Mc=%.2f)", b, sigma_b, n, mc)
        return (float(b), float(sigma_b))

    def completeness_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Строит матрицу Mc по регионам × десятилетиям.

        Args:
            df: DataFrame с колонками year, fe_region, magnitude.

        Returns:
            DataFrame с регионами по строкам и десятилетиями по столбцам.
        """
        if "fe_region" not in df.columns:
            logger.warning("Колонка fe_region отсутствует")
            return pd.DataFrame()

        # Десятилетия
        year_min = int(df["year"].min())
        year_max = int(df["year"].max())
        decades = list(range((year_min // 10) * 10, year_max + 10, 10))
        regions = sorted(df["fe_region"].dropna().unique().astype(int))

        matrix: dict[str, list[float]] = {"decade": []}
        for reg in regions:
            matrix[f"reg_{reg}"] = []

        for dec_start in decades[:-1]:
            dec_end = dec_start + 9
            matrix["decade"].append(dec_start)
            for reg in regions:
                mc = self.estimate_mc(
                    df, region=int(reg),
                    period_start=dec_start,
                    period_end=dec_end,
                )
                matrix[f"reg_{reg}"].append(mc)

        result = pd.DataFrame(matrix).set_index("decade")
        logger.info(
            "Матрица полноты: %d десятилетий × %d регионов",
            len(decades) - 1, len(regions),
        )
        return result

    def weight_by_completeness(
        self,
        df: pd.DataFrame,
        matrix: pd.DataFrame,
    ) -> pd.DataFrame:
        """Добавляет колонку completeness_weight к каждому событию.

        Вес = 1 если магнитуда >= Mc для данного региона и периода,
        иначе уменьшается пропорционально разности.

        Args:
            df: DataFrame с событиями (year, fe_region, magnitude).
            matrix: матрица Mc из completeness_matrix().

        Returns:
            DataFrame с новой колонкой completeness_weight.
        """
        df = df.copy()
        weights = np.ones(len(df))

        for i, row in df.iterrows():
            year = row.get("year")
            reg = row.get("fe_region")
            mag = row.get("magnitude")

            if pd.isna(year) or pd.isna(reg) or pd.isna(mag):
                weights[i] = 0.0
                continue

            decade = int((int(year) // 10) * 10)
            col = f"reg_{int(reg)}"

            if decade not in matrix.index or col not in matrix.columns:
                weights[i] = 0.5  # умеренный вес при отсутствии оценки
                continue

            mc = matrix.loc[decade, col]
            if mag >= mc:
                weights[i] = 1.0
            else:
                weights[i] = max(0.0, 1.0 - (mc - mag))

        df["completeness_weight"] = weights
        return df

    @staticmethod
    def _filter(
        df: pd.DataFrame,
        region: int | None,
        period_start: int | None,
        period_end: int | None,
    ) -> pd.DataFrame:
        """Фильтрует DataFrame по региону и временному периоду."""
        sub = df.copy()
        if region is not None and "fe_region" in sub.columns:
            sub = sub[sub["fe_region"] == region]
        if period_start is not None:
            sub = sub[sub["year"] >= period_start]
        if period_end is not None:
            sub = sub[sub["year"] <= period_end]
        return sub
