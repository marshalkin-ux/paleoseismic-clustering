"""Загрузчик исторического каталога NOAA NGDC.

Скачивает данные от ~2150 BCE по настоящее время через NOAA NGDC API.
"""

from __future__ import annotations

import json
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

BASE_URL = "https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/earthquakes"
RAW_DIR = Path(__file__).parents[2] / "data" / "raw" / "noaa"


class NOAAFetcher:
    """Загрузчик исторического каталога NOAA NGDC (от ~2150 BCE).

    Пример::

        fetcher = NOAAFetcher()
        fetcher.fetch()
        df = fetcher.to_dataframe()
    """

    def __init__(self, raw_dir: Path | None = None) -> None:
        self.raw_dir = raw_dir or RAW_DIR
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self._raw_data: list[dict[str, Any]] = []

    def fetch(self, min_magnitude: float = 6.0) -> None:
        """Скачивает полный исторический каталог NOAA NGDC.

        Args:
            min_magnitude: минимальная магнитуда для фильтрации.
        """
        self._raw_data = []
        page = 1
        page_size = 1000

        while True:
            params: dict[str, Any] = {
                "minMagnitude": min_magnitude,
                "pageNumber": page,
                "pageSize": page_size,
            }
            data = self._request_with_retry(BASE_URL, params)
            if data is None:
                break

            items = data.get("items", [])
            if not items:
                break

            self._raw_data.extend(items)

            fname = self.raw_dir / f"noaa_page{page:04d}.json"
            fname.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
            logger.debug("Страница %d: %d событий", page, len(items))

            if len(items) < page_size:
                break
            page += 1

        logger.info("Загружено событий NOAA: %d", len(self._raw_data))

    def _request_with_retry(
        self,
        url: str,
        params: dict[str, Any],
        max_retries: int = 3,
    ) -> dict[str, Any] | None:
        """Запрос к API с экспоненциальным backoff."""
        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.get(url, params=params, timeout=60)
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.HTTPError as exc:
                logger.warning(
                    "HTTP-ошибка %s (попытка %d/%d)",
                    exc.response.status_code, attempt, max_retries,
                )
            except requests.exceptions.RequestException as exc:
                logger.warning("Ошибка сети (попытка %d/%d): %s", attempt, max_retries, exc)

            if attempt < max_retries:
                time.sleep(2 ** attempt)

        return None

    def to_dataframe(self) -> pd.DataFrame:
        """Возвращает события в унифицированном формате.

        year_error: 50 лет для BCE, 10 лет для 1-1900, 1 год для >1900.
        quality_score: 0.3 для BCE, 0.6 для 1000-1900, 0.9 для >1900.
        """
        if not self._raw_data:
            self._load_from_disk()

        rows: list[dict[str, Any]] = []
        for item in self._raw_data:
            year_raw = item.get("year")
            if year_raw is None:
                continue
            year = int(year_raw)

            # Оценка погрешности и качества по эпохе
            if year < 0:
                year_error = 50
                quality = 0.3
                src_type = "paleoseismic"
            elif year < 1000:
                year_error = 20
                quality = 0.4
                src_type = "historical"
            elif year < 1900:
                year_error = 10
                quality = 0.6
                src_type = "historical"
            else:
                year_error = 1
                quality = 0.9
                src_type = "instrumental"

            mag_raw = item.get("eqMagnitude")
            magnitude = float(mag_raw) if mag_raw is not None else None

            rows.append({
                "event_id": f"noaa_{item.get('id', '')}",
                "year": year,
                "year_error": year_error,
                "month": item.get("month"),
                "day": item.get("day"),
                "lat": item.get("latitude"),
                "lon": item.get("longitude"),
                "magnitude": magnitude,
                "magnitude_error": None,
                "depth_km": item.get("focal_depth"),
                "region": item.get("locationName", ""),
                "source_type": src_type,
                "reference": "NOAA NGDC",
                "quality_score": quality,
            })

        return pd.DataFrame(rows, columns=UNIFIED_COLUMNS)

    def _load_from_disk(self) -> None:
        """Загружает сохранённые страницы из raw_dir."""
        files = sorted(self.raw_dir.glob("noaa_page*.json"))
        if not files:
            logger.warning("Нет файлов NOAA в %s", self.raw_dir)
            return
        for f in files:
            items = json.loads(f.read_text(encoding="utf-8"))
            self._raw_data.extend(items)
        logger.info("Загружено %d событий из %d файлов NOAA", len(self._raw_data), len(files))
