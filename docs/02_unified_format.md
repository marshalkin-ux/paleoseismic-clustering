# 02. Унифицированный формат каталога

Все загруженные события из разных источников приводятся к единой схеме `unified_catalog` перед анализом. Унификация выполняется классом `CatalogUnifier` и включает нормализацию полей, конвертацию магнитуд к `Mw`, пространственно-временную дедупликацию и расчёт интегрального `quality_score`.

---

## 2.1 Описание полей unified_catalog.csv

| Поле | Тип | Описание | Пример |
|------|-----|---------|--------|
| `event_id` | str | Уникальный идентификатор события (UUID4) | `a1b2c3d4-e5f6-...` |
| `year` | int | Год события | `1906` |
| `year_error` | float | Погрешность года (лет), для исторических событий | `0.0` / `2.5` |
| `month` | int | Месяц (1–12); `null` если неизвестен | `4` |
| `day` | int | День (1–31); `null` если неизвестен | `18` |
| `lat` | float | Широта эпицентра, градусы WGS-84 | `37.7` |
| `lon` | float | Долгота эпицентра, градусы WGS-84 | `-122.5` |
| `magnitude` | float | Моментная магнитуда Mw (конвертированная) | `7.9` |
| `magnitude_error` | float | Погрешность магнитуды | `0.2` |
| `depth_km` | float | Глубина очага, км; `null` если неизвестна | `10.0` |
| `region` | str | Географическое название региона | `"Northern California"` |
| `flinn_engdahl_region` | int | Номер региона Флинна–Энгдала (1–757) | `71` |
| `source_type` | str | Источник данных: `usgs`, `noaa`, `isc` | `"isc"` |
| `reference` | str | Библиографическая ссылка / DOI | `"ISC Bulletin 2024"` |
| `quality_score` | float | Интегральная оценка качества (0–4) | `3.5` |

### Примечания к полям

- **`event_id`**: генерируется при первом добавлении события; при дедупликации сохраняется ID источника с наивысшим приоритетом.
- **`flinn_engdahl_region`**: определяется автоматически по координатам (`(lat, lon) → FE region`). Используется для критерия "≥3 регионов" при идентификации глобальных серий.
- **`quality_score`**: взвешенная сумма: инструментальность (0–2) + число станций (0–1) + перекрёстная верификация (0–1).
- **`magnitude`**: все магнитуды конвертированы к `Mw` по формулам Scordilis (2006) и Weatherill et al. (2016). Исходный тип хранится в дополнительной колонке `mag_type_original`.

---

## 2.2 Процедура дедупликации

Дедупликация удаляет дублирующиеся записи, возникающие из-за пересечения каталогов. Применяются два порога одновременно:

### Критерии дедупликата

Два события считаются дублями, если выполнены **оба** условия:

1. **Пространственный порог**: расстояние между эпицентрами ≤ **50 км** (геодезическое).
2. **Временной порог**: |t1 − t2| ≤ **30 дней**.

### Приоритет источников

При обнаружении дубля сохраняется запись из источника с наивысшим приоритетом:

```
ISC > USGS > NOAA
```

Параметры очага (lat, lon, depth, magnitude) берутся из приоритетного источника; `quality_score` пересчитывается с учётом факта перекрёстной верификации (+0.5).

### Алгоритм

```python
from scipy.spatial import cKDTree
import numpy as np

def deduplicate(df: pd.DataFrame,
                spatial_km: float = 50.0,
                temporal_days: float = 30.0) -> pd.DataFrame:
    """
    Пространственно-временная дедупликация каталога.

    Параметры
    ---------
    df : pd.DataFrame
        Унифицированный каталог (должен содержать lat, lon, year, month, day).
    spatial_km : float
        Пространственный порог в км.
    temporal_days : float
        Временной порог в днях.

    Возвращает
    ----------
    pd.DataFrame
        Каталог без дублей.
    """
    PRIORITY = {"isc": 0, "usgs": 1, "noaa": 2}
    df = df.sort_values("source_type", key=lambda s: s.map(PRIORITY))

    coords_rad = np.radians(df[["lat", "lon"]].values)
    # KDTree на единичной сфере (угловое расстояние -> км)
    R_EARTH_KM = 6371.0
    threshold_rad = spatial_km / R_EARTH_KM

    tree = cKDTree(coords_rad)
    pairs = tree.query_pairs(r=threshold_rad)

    drop_indices = set()
    for i, j in pairs:
        t_diff = abs(df.iloc[i]["_day_of_year"] - df.iloc[j]["_day_of_year"])
        if t_diff <= temporal_days and j not in drop_indices:
            drop_indices.add(j)

    return df.drop(df.index[list(drop_indices)]).reset_index(drop=True)
```

---

## 2.3 Схема SQLite базы данных

Помимо CSV, данные хранятся в SQLite-базе `seismic_catalog.db` для эффективных запросов.

```sql
-- Основная таблица событий
CREATE TABLE IF NOT EXISTS events (
    event_id            TEXT PRIMARY KEY,
    year                INTEGER NOT NULL,
    year_error          REAL    DEFAULT 0.0,
    month               INTEGER,
    day                 INTEGER,
    lat                 REAL    NOT NULL,
    lon                 REAL    NOT NULL,
    magnitude           REAL    NOT NULL,
    magnitude_error     REAL    DEFAULT 0.2,
    depth_km            REAL,
    region              TEXT,
    flinn_engdahl_region INTEGER,
    source_type         TEXT    NOT NULL CHECK (source_type IN ('usgs', 'noaa', 'isc')),
    reference           TEXT,
    quality_score       REAL    NOT NULL DEFAULT 0.0,
    created_at          TEXT    DEFAULT (datetime('now')),
    mag_type_original   TEXT
);

-- Индексы для ускорения пространственно-временных запросов
CREATE INDEX IF NOT EXISTS idx_events_year       ON events (year);
CREATE INDEX IF NOT EXISTS idx_events_lat_lon    ON events (lat, lon);
CREATE INDEX IF NOT EXISTS idx_events_magnitude  ON events (magnitude);
CREATE INDEX IF NOT EXISTS idx_events_fe_region  ON events (flinn_engdahl_region);
CREATE INDEX IF NOT EXISTS idx_events_quality    ON events (quality_score);

-- Таблица глобальных серий (результат анализа)
CREATE TABLE IF NOT EXISTS seismic_series (
    series_id       TEXT PRIMARY KEY,
    window_start    TEXT NOT NULL,   -- ISO8601 дата начала окна
    window_end      TEXT NOT NULL,
    n_events        INTEGER NOT NULL,
    max_magnitude   REAL NOT NULL,
    n_fe_regions    INTEGER NOT NULL,
    p_value         REAL,
    eta_threshold   REAL,
    description     TEXT
);

-- Связь событий с сериями (many-to-many)
CREATE TABLE IF NOT EXISTS series_events (
    series_id   TEXT NOT NULL REFERENCES seismic_series(series_id),
    event_id    TEXT NOT NULL REFERENCES events(event_id),
    eta_to_prev REAL,            -- η к предыдущему событию серии
    PRIMARY KEY (series_id, event_id)
);

-- Таблица истории дедупликации (аудит)
CREATE TABLE IF NOT EXISTS dedup_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    kept_event_id   TEXT NOT NULL REFERENCES events(event_id),
    dropped_event_id TEXT NOT NULL,
    spatial_dist_km  REAL,
    temporal_diff_days REAL,
    processed_at    TEXT DEFAULT (datetime('now'))
);
```