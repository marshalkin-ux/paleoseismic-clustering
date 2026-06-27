"""Унификатор и объединитель каталогов землетрясений.

Объединяет данные из USGS, NOAA и ISC, устраняет дубликаты
и назначает регионы Flinn-Engdahl.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

logger = logging.getLogger(__name__)

UNIFIED_COLUMNS = [
    "event_id", "year", "year_error", "month", "day",
    "lat", "lon", "magnitude", "magnitude_error", "depth_km",
    "region", "source_type", "reference", "quality_score",
    "fe_region",
]

# Приоритеты источников при дедупликации (больше = выше приоритет)
SOURCE_PRIORITY = {
    "ISC Bulletin": 3,
    "USGS ComCat": 2,
    "NOAA NGDC": 1,
}

# Упрощённая таблица регионов Flinn-Engdahl (50 регионов)
# Формат: (номер, название, центр lat, центр lon)
FE_REGIONS: list[tuple[int, str, float, float]] = [
    (1,  "Alaska-Aleutian Arc",               56.0,  -155.0),
    (2,  "Southeastern Alaska, British Columbia", 56.0, -132.0),
    (3,  "California-Nevada Region",           37.0,  -120.0),
    (4,  "Baja California",                   28.0,  -113.0),
    (5,  "Mexico-Guatemala Area",              16.0,   -92.0),
    (6,  "Central America",                    10.0,   -84.0),
    (7,  "Caribbean Loop",                     15.0,   -70.0),
    (8,  "Andean South America N",             -5.0,   -77.0),
    (9,  "Andean South America S",            -30.0,   -70.0),
    (10, "Southern Andes",                    -45.0,   -73.0),
    (11, "Scotia Arc",                        -57.0,   -28.0),
    (12, "Atlantic Ocean",                     10.0,   -30.0),
    (13, "Iceland Region",                    65.0,   -18.0),
    (14, "Northern Europe",                   57.0,    15.0),
    (15, "Western Mediterranean",             38.0,     5.0),
    (16, "Eastern Mediterranean",             37.0,    28.0),
    (17, "North Africa",                      28.0,    15.0),
    (18, "East Africa Rift",                   0.0,    35.0),
    (19, "Middle East",                       33.0,    50.0),
    (20, "Caucasus-Turkey",                   40.0,    42.0),
    (21, "Iran-Afghanistan",                  32.0,    60.0),
    (22, "Hindukush-Pamir",                   37.0,    70.0),
    (23, "Northern India-Nepal",              28.0,    82.0),
    (24, "Assam-Myanmar",                     23.0,    93.0),
    (25, "Indian Ocean",                     -10.0,    75.0),
    (26, "Pakistan",                          27.0,    67.0),
    (27, "Kazakhstan-Central Asia",           43.0,    68.0),
    (28, "Altai-Baikal",                      51.0,   102.0),
    (29, "Northeastern Asia",                 60.0,   140.0),
    (30, "Kuril-Kamchatka Arc",               50.0,   155.0),
    (31, "Japan",                             36.0,   138.0),
    (32, "Ryukyu Arc",                        25.0,   127.0),
    (33, "Taiwan",                            24.0,   122.0),
    (34, "South China Sea",                   16.0,   115.0),
    (35, "Philippines",                       12.0,   124.0),
    (36, "Sulawesi",                          -1.5,   121.0),
    (37, "Banda Sea",                         -7.0,   128.0),
    (38, "New Guinea",                        -5.0,   142.0),
    (39, "Solomon Islands",                   -9.0,   159.0),
    (40, "Vanuatu",                          -15.0,   167.0),
    (41, "Tonga-Kermadec",                   -25.0,  -175.0),
    (42, "New Zealand",                      -40.0,   177.0),
    (43, "Sumatra",                           -3.0,   104.0),
    (44, "Java",                              -7.0,   112.0),
    (45, "Andaman Islands",                   12.0,    93.0),
    (46, "Himalaya-Tibet",                    32.0,    88.0),
    (47, "Western China-Mongolia",            44.0,    88.0),
    (48, "Arabian Peninsula",                 22.0,    45.0),
    (49, "Red Sea",                           22.0,    38.0),
    (50, "Pacific Ocean",                      0.0,  -160.0),
]


class CatalogUnifier:
    """Объединяет каталоги из нескольких источников.

    Пример::

        unifier = CatalogUnifier()
        merged = unifier.merge([df_usgs, df_noaa, df_isc])
        unifier.save(merged, Path("data/processed/unified.csv"))
    """

    def __init__(
        self,
        spatial_threshold_km: float = 50.0,
        time_threshold_days: float = 30.0,
    ) -> None:
        self.spatial_threshold_km = spatial_threshold_km
        self.time_threshold_days = time_threshold_days

        # Предвычисляем KD-дерево для Flinn-Engdahl регионов
        self._fe_coords = np.array([(r[2], r[3]) for r in FE_REGIONS])
        self._fe_tree = cKDTree(self._fe_coords)

    def merge(self, dataframes: list[pd.DataFrame]) -> pd.DataFrame:
        """Объединяет несколько каталогов, устраняя дубликаты.

        События считаются дублями, если они находятся в пределах
        50 км и 30 дней друг от друга. При конфликте приоритет
        отдаётся источнику с более высоким рейтингом: ISC > USGS > NOAA.

        Args:
            dataframes: список DataFrame в унифицированном формате.

        Returns:
            Объединённый DataFrame без дубликатов.
        """
        if not dataframes:
            return pd.DataFrame(columns=UNIFIED_COLUMNS)

        # Сортируем по приоритету источника (высший приоритет — последним,
        # чтобы при drop_duplicates сохранялась наиболее достоверная запись)
        tagged: list[pd.DataFrame] = []
        for df in dataframes:
            df = df.copy()
            df["_priority"] = df["reference"].map(SOURCE_PRIORITY).fillna(0)
            tagged.append(df)

        combined = pd.concat(tagged, ignore_index=True)
        combined = combined.dropna(subset=["lat", "lon", "year"])
        combined = combined.sort_values("_priority", ascending=False).reset_index(drop=True)

        logger.info("Всего событий до дедупликации: %d", len(combined))
        deduped = self._deduplicate(combined)
        logger.info("После дедупликации: %d событий", len(deduped))

        deduped = self.assign_flinn_engdahl(deduped)
        deduped = deduped.drop(columns=["_priority"], errors="ignore")
        return deduped.reset_index(drop=True)

    def _deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Удаляет дублирующие события по пространственно-временному критерию."""
        # Приводим координаты к радианам для haversine
        lat_rad = np.radians(df["lat"].values)
        lon_rad = np.radians(df["lon"].values)

        # Приблизительный перевод порога в радианы (для KD-дерева)
        r_earth = 6371.0
        threshold_rad = self.spatial_threshold_km / r_earth

        # Строим KD-дерево по (lat_rad, lon_rad)
        coords = np.column_stack([lat_rad, lon_rad])
        tree = cKDTree(coords)

        # Дни от начала эпохи (для временного сравнения)
        days = self._to_julian_days(df)

        kept = np.ones(len(df), dtype=bool)
        for i in range(len(df)):
            if not kept[i]:
                continue
            # Соседи в пределах пространственного порога
            neighbors = tree.query_ball_point(coords[i], r=threshold_rad * 1.5)
            for j in neighbors:
                if j <= i or not kept[j]:
                    continue
                # Временная проверка
                if abs(days[i] - days[j]) <= self.time_threshold_days:
                    # Оставляем событие с меньшим индексом (более высокий приоритет)
                    kept[j] = False

        return df[kept].copy()

    @staticmethod
    def _to_julian_days(df: pd.DataFrame) -> np.ndarray:
        """Вычисляет приблизительные юлианские дни для каждого события."""
        year = df["year"].fillna(0).astype(float).values
        month = df["month"].fillna(6).astype(float).values
        day = df["day"].fillna(15).astype(float).values
        return year * 365.25 + (month - 1) * 30.44 + day

    def assign_flinn_engdahl(self, df: pd.DataFrame) -> pd.DataFrame:
        """Назначает номер и название региона Flinn-Engdahl каждому событию.

        Args:
            df: DataFrame с колонками lat, lon.

        Returns:
            DataFrame с добавленными колонками fe_region (номер) и region
            (обновлённое название, если оно пустое).
        """
        coords = df[["lat", "lon"]].fillna(0).values
        _, indices = self._fe_tree.query(coords)

        fe_nums = [FE_REGIONS[i][0] for i in indices]
        fe_names = [FE_REGIONS[i][1] for i in indices]

        df = df.copy()
        df["fe_region"] = fe_nums

        # Обновляем название региона только если оно пустое
        mask = df["region"].isna() | (df["region"] == "")
        df.loc[mask, "region"] = [fe_names[i] for i, m in enumerate(mask) if m]

        return df

    def save(self, df: pd.DataFrame, path: Path) -> None:
        """Сохраняет объединённый каталог в CSV и SQLite.

        Args:
            df: объединённый DataFrame.
            path: путь к CSV-файлу (SQLite сохраняется рядом с расширением .db).
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        df.to_csv(path, index=False, encoding="utf-8")
        logger.info("Каталог сохранён в CSV: %s", path)

        db_path = path.with_suffix(".db")
        try:
            from sqlalchemy import create_engine
            engine = create_engine(f"sqlite:///{db_path}")
            df.to_sql("events", engine, if_exists="replace", index=False)
            engine.dispose()
            logger.info("Каталог сохранён в SQLite: %s", db_path)
        except ImportError:
            logger.warning("SQLAlchemy недоступна, SQLite не сохранён")
