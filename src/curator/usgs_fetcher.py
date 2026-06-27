"""Загрузчик данных USGS ComCat API.

Скачивает каталог землетрясений через earthquake.usgs.gov постранично
по 5-летним чанкам и сохраняет JSON-файлы в data/raw/usgs/.
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

BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
RAW_DIR = Path(__file__).parents[2] / "data" / "raw" / "usgs"


class USGSFetcher:
    """Агент-куратор: загрузчик каталога USGS ComCat.

    Пример использования::

        fetcher = USGSFetcher()
        fetcher.fetch(min_magnitude=6.5, start_year=1900, end_year=2026)
        df = fetcher.to_dataframe()
    """

    def __init__(self, raw_dir: Path | str | None = None) -> None:
        self.raw_dir = Path(raw_dir) if raw_dir is not None else Path(RAW_DIR)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self._records: list[dict[str, Any]] = []

    def fetch(
        self,
        min_magnitude: float = 6.5,
        start_year: int = 1900,
        end_year: int = 2026,
        chunk_years: int = 5,
    ) -> None:
        """Скачивает события из USGS ComCat API по временным чанкам.

        Args:
            min_magnitude: минимальная магнитуда.
            start_year: начальный год выборки.
            end_year: конечный год (включительно).
            chunk_years: размер чанка в годах.
        """
        self._records = []
        for chunk_start in range(start_year, end_year + 1, chunk_years):
            chunk_end = min(chunk_start + chunk_years - 1, end_year)
            self._fetch_chunk(
                min_magnitude=min_magnitude,
                start_date=f"{chunk_start}-01-01",
                end_date=f"{chunk_end}-12-31",
            )
        logger.info("Загружено событий USGS: %d", len(self._records))

    def _fetch_chunk(
        self,
        min_magnitude: float,
        start_date: str,
        end_date: str,
    ) -> None:
        """Загружает один временной чанк с постраничной разбивкой."""
        offset = 1
        limit = 20000

        while True:
            params: dict[str, Any] = {
                "format": "geojson",
                "starttime": start_date,
                "endtime": end_date,
                "minmagnitude": min_magnitude,
                "limit": limit,
                "offset": offset,
                "orderby": "time-asc",
            }
            data = self._request_with_retry(BASE_URL, params)
            if data is None:
                break

            features = data.get("features", [])
            if not features:
                break

            fname = self.raw_dir / f"usgs_{start_date}_{end_date}_off{offset}.json"
            fname.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            logger.debug("Сохранён файл: %s (%d событий)", fname.name, len(features))

            self._records.extend(features)
            if len(features) < limit:
                break
            offset += limit

    def _request_with_retry(
        self,
        url: str,
        params: dict[str, Any],
        max_retries: int = 3,
    ) -> dict[str, Any] | None:
        """Запрос к API с экспоненциальным backoff при ошибках сети."""
        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.get(url, params=params, timeout=120)
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.HTTPError as exc:
                logger.warning(
                    "HTTP-ошибка %s (попытка %d/%d): %s",
                    exc.response.status_code, attempt, max_retries, exc,
                )
                if exc.response.status_code == 400:
                    return None
            except requests.exceptions.RequestException as exc:
                logger.warning(
                    "Ошибка запроса (попытка %d/%d): %s",
                    attempt, max_retries, exc,
                )

            if attempt < max_retries:
                sleep_t = 2 ** attempt
                logger.info("Повтор через %d сек...", sleep_t)
                time.sleep(sleep_t)

        logger.error("Все %d попыток исчерпаны.", max_retries)
        return None

    def to_dataframe(self) -> pd.DataFrame:
        """Возвращает события в унифицированном формате DataFrame."""
        if not self._records:
            self._load_from_disk()

        rows: list[dict[str, Any]] = []
        for feat in self._records:
            props = feat.get("properties", {})
            geom = feat.get("geometry", {})
            coords = geom.get("coordinates", [None, None, None])

            time_ms = props.get("time")
            if time_ms is None:
                continue
            dt = pd.to_datetime(time_ms, unit="ms", utc=True)

            rows.append({
                "event_id": feat.get("id", ""),
                "year": int(dt.year),
                "year_error": 0,
                "month": int(dt.month),
                "day": int(dt.day),
                "lat": coords[1],
                "lon": coords[0],
                "magnitude": props.get("mag"),
                "magnitude_error": props.get("magError"),
                "depth_km": coords[2],
                "region": props.get("place", ""),
                "source_type": "instrumental",
                "reference": "USGS ComCat",
                "quality_score": 0.95 if props.get("status") == "reviewed" else 0.80,
            })

        return pd.DataFrame(rows, columns=UNIFIED_COLUMNS)

    def _load_from_disk(self) -> None:
        """Загружает ранее сохранённые JSON-файлы из raw_dir."""
        files = sorted(self.raw_dir.glob("usgs_*.json"))
        if not files:
            logger.warning("Нет сохранённых файлов USGS в %s", self.raw_dir)
            return
        for f in files:
            data = json.loads(f.read_text(encoding="utf-8"))
            self._records.extend(data.get("features", []))
        logger.info("Загружено %d событий из %d файлов", len(self._records), len(files))
