"""Загрузчик данных ISC Bulletin.

Скачивает каталог из International Seismological Centre через web-db API.
"""

from __future__ import annotations

import io
import logging
import time
from pathlib import Path
from typing import Any

import pandas as pd
import requests

logger = logging.getLogger(__name__)

UNIFIED_COLUMNS = [
    "event_id", "year", "year_error", "month", "day",
    "lat", "lon", "magnitude", "magnitude_error", "depth_km",
    "region", "source_type", "reference", "quality_score",
]

ISC_URL = "http://www.isc.ac.uk/cgi-bin/web-db-v4"
RAW_DIR = Path(__file__).parents[2] / "data" / "raw" / "isc"


class ISCFetcher:
    """Загрузчик каталога ISC Bulletin (M >= 6.5 с 1900 г.).

    Пример::

        fetcher = ISCFetcher()
        fetcher.fetch(min_magnitude=6.5)
        df = fetcher.to_dataframe()
    """

    def __init__(self, raw_dir: Path | None = None) -> None:
        self.raw_dir = raw_dir or RAW_DIR
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self._dataframes: list[pd.DataFrame] = []

    def fetch(
        self,
        min_magnitude: float = 6.5,
        start_year: int = 1900,
        end_year: int = 2024,
        chunk_years: int = 10,
    ) -> None:
        """Запрашивает ISC Bulletin чанками по 10 лет.

        Args:
            min_magnitude: минимальная магнитуда.
            start_year: год начала.
            end_year: год конца.
            chunk_years: размер чанка в годах.
        """
        self._dataframes = []
        for yr in range(start_year, end_year + 1, chunk_years):
            yr_end = min(yr + chunk_years - 1, end_year)
            df = self._fetch_chunk(min_magnitude, yr, yr_end)
            if df is not None and not df.empty:
                self._dataframes.append(df)

        total = sum(len(d) for d in self._dataframes)
        logger.info("Загружено событий ISC: %d", total)

    def _fetch_chunk(
        self,
        min_magnitude: float,
        start_year: int,
        end_year: int,
    ) -> pd.DataFrame | None:
        """Загружает один чанк из ISC Bulletin."""
        params: dict[str, Any] = {
            "request": "BULLETIN",
            "out_format": "CSV",
            "starttime": f"{start_year}-01-01",
            "endtime": f"{end_year}-12-31",
            "minmag": min_magnitude,
            "magtype": "MW",
            "searchshape": "GLOBAL",
            "prime_only": "on",
        }

        raw_text = self._request_with_retry(ISC_URL, params)
        if raw_text is None:
            return None

        # Сохраняем на диск
        fname = self.raw_dir / f"isc_{start_year}_{end_year}.csv"
        fname.write_text(raw_text, encoding="utf-8")
        logger.debug("ISC чанк %d-%d сохранён", start_year, end_year)

        return self._parse_csv(raw_text)

    def _request_with_retry(
        self,
        url: str,
        params: dict[str, Any],
        max_retries: int = 3,
    ) -> str | None:
        """Запрос к ISC с backoff."""
        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.get(url, params=params, timeout=180)
                resp.raise_for_status()
                return resp.text
            except requests.exceptions.RequestException as exc:
                logger.warning("ISC ошибка (попытка %d/%d): %s", attempt, max_retries, exc)
            if attempt < max_retries:
                time.sleep(2 ** attempt)
        return None

    def _parse_csv(self, raw_text: str) -> pd.DataFrame:
        """Парсит CSV-ответ ISC Bulletin."""
        lines = raw_text.splitlines()
        # Ищем начало данных (строка с заголовком EVENTID)
        header_idx = None
        for i, line in enumerate(lines):
            if "EVENTID" in line:
                header_idx = i
                break

        if header_idx is None:
            logger.warning("Не найден заголовок ISC CSV")
            return pd.DataFrame()

        csv_text = "\n".join(lines[header_idx:])
        try:
            df = pd.read_csv(io.StringIO(csv_text), skipinitialspace=True)
        except Exception as exc:
            logger.error("Ошибка парсинга ISC CSV: %s", exc)
            return pd.DataFrame()

        return df

    def to_dataframe(self) -> pd.DataFrame:
        """Возвращает объединённый DataFrame в унифицированном формате."""
        if not self._dataframes:
            self._load_from_disk()

        if not self._dataframes:
            return pd.DataFrame(columns=UNIFIED_COLUMNS)

        raw = pd.concat(self._dataframes, ignore_index=True)
        rows: list[dict[str, Any]] = []

        for _, row in raw.iterrows():
            try:
                lat = float(row.get("LAT", row.get("lat", float("nan"))))
                lon = float(row.get("LON", row.get("lon", float("nan"))))
                mag = row.get("MAGNITUDE", row.get("mag"))
                depth = row.get("DEPTH", row.get("depth"))
                ev_id = str(row.get("EVENTID", row.get("eventid", "")))

                # Дата
                year = int(row.get("YEAR", row.get("year", 0)))
                month_raw = row.get("MONTH", row.get("month"))
                day_raw = row.get("DAY", row.get("day"))

                rows.append({
                    "event_id": f"isc_{ev_id}",
                    "year": year,
                    "year_error": 0,
                    "month": int(month_raw) if pd.notna(month_raw) else None,
                    "day": int(day_raw) if pd.notna(day_raw) else None,
                    "lat": lat,
                    "lon": lon,
                    "magnitude": float(mag) if pd.notna(mag) else None,
                    "magnitude_error": None,
                    "depth_km": float(depth) if pd.notna(depth) else None,
                    "region": str(row.get("REGION", "")),
                    "source_type": "instrumental",
                    "reference": "ISC Bulletin",
                    "quality_score": 0.90,
                })
            except (ValueError, TypeError) as exc:
                logger.debug("Пропущена строка ISC: %s", exc)

        return pd.DataFrame(rows, columns=UNIFIED_COLUMNS)

    def _load_from_disk(self) -> None:
        """Загружает сохранённые CSV-файлы ISC."""
        files = sorted(self.raw_dir.glob("isc_*.csv"))
        if not files:
            logger.warning("Нет файлов ISC в %s", self.raw_dir)
            return
        for f in files:
            df = self._parse_csv(f.read_text(encoding="utf-8"))
            if not df.empty:
                self._dataframes.append(df)
        logger.info("Загружено ISC из %d файлов", len(files))
