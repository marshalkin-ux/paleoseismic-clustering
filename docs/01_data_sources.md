# 01. Источники данных

В проекте используются четыре независимых каталога сейсмических событий. Комбинирование источников позволяет увеличить временной охват (до ~1900 года для инструментальных данных и до ~1600 года для исторических событий M≥7), снизить пропуски событий и перекрёстно верифицировать параметры очагов.

---

## 1.1 USGS ComCat API

**URL**: `https://earthquake.usgs.gov/fdsnws/event/1/query`

### Параметры запроса

| Параметр | Тип | Описание | Пример |
|----------|-----|---------|--------|
| `format` | str | Формат ответа | `geojson` |
| `starttime` | ISO8601 | Начало периода | `1900-01-01` |
| `endtime` | ISO8601 | Конец периода | `2024-12-31` |
| `minmagnitude` | float | Минимальная магнитуда | `5.0` |
| `maxdepth` | float | Максимальная глубина, км | `700` |
| `orderby` | str | Сортировка | `time` |
| `limit` | int | Лимит записей | `20000` |
| `offset` | int | Смещение (для пагинации) | `0` |

> **Ограничение**: максимум **20 000 событий** на один запрос. Для получения полного каталога необходима пагинация по временным окнам (рекомендуется шаг 5 лет для M≥5).

### Пример ответа (GeoJSON)

```json
{
  "type": "FeatureCollection",
  "metadata": {
    "count": 2,
    "status": 200,
    "url": "https://earthquake.usgs.gov/fdsnws/event/1/query?..."
  },
  "features": [
    {
      "type": "Feature",
      "properties": {
        "mag": 6.7,
        "place": "126 km SSE of Ust'-Kamchatsk Staryy, Russia",
        "time": 1704067200000,
        "updated": 1704153600000,
        "tz": null,
        "url": "https://earthquake.usgs.gov/earthquakes/eventpage/us7000m0gg",
        "detail": "...",
        "felt": null,
        "cdi": null,
        "mmi": 4.5,
        "alert": null,
        "status": "reviewed",
        "tsunami": 0,
        "sig": 691,
        "net": "us",
        "code": "7000m0gg",
        "ids": ",us7000m0gg,",
        "sources": ",us,",
        "types": ",origin,phase-data,",
        "nst": 142,
        "dmin": 1.847,
        "rms": 0.87,
        "gap": 24,
        "magType": "mww",
        "type": "earthquake",
        "title": "M 6.7 - 126 km SSE of Ust'-Kamchatsk"
      },
      "geometry": {
        "type": "Point",
        "coordinates": [163.4521, 50.7894, 35.0]
      },
      "id": "us7000m0gg"
    }
  ]
}
```

### Временной охват и ограничения

- **Инструментальный период**: 1900 — настоящее время (качество данных резко улучшается после ~1960).
- **Полнота**: M≥5.0 глобально с ~1976 (введение WWSSN-сети), M≥6.5 с ~1900.
- **Rate limit**: 1 запрос в секунду; при превышении возвращается HTTP 429.
- **Максимум событий**: 20 000 на запрос; реализована пагинация по `offset`.
- **Типы магнитуд**: `mww`, `mw`, `mb`, `ms`, `ml` — унифицируются к `Mw` по таблицам Scordilis (2006).

---

## 1.2 NOAA NGDC (National Geophysical Data Center)

**URL**: `https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/earthquakes`

### Параметры запроса

| Параметр | Тип | Описание |
|----------|-----|---------|
| `minYear` | int | Начальный год |
| `maxYear` | int | Конечный год |
| `minMagnitude` | float | Минимальная магнитуда |
| `country` | str | Страна (опционально) |

### Формат ответа

Ответ возвращается в **JSON** со структурой:

```json
{
  "count": 150,
  "items": [
    {
      "id": 5560,
      "year": 1906,
      "month": 4,
      "day": 18,
      "hour": 13,
      "minute": 12,
      "second": 21.0,
      "latitude": 37.7,
      "longitude": -122.5,
      "focal_depth": 10,
      "eq_primary": 7.9,
      "intensity": 11,
      "country": "USA",
      "location_name": "SAN FRANCISCO, CA",
      "deaths": 3000,
      "injuries": null,
      "damage_millions_dollars": 524.0
    }
  ]
}
```

### Историческая достоверность и quality_score

NOAA NGDC охватывает **исторические события с ~1600 года**, однако качество параметров неоднородно. Используется внутренняя шкала `quality_score`:

| Балл | Описание | Примерный период |
|------|---------|-----------------|
| 4 | Инструментальные данные, несколько сейсмограмм | 1964 — н.в. |
| 3 | Инструментальные данные, единичные станции | 1900–1963 |
| 2 | Макросейсмические данные, хорошая документация | 1750–1899 |
| 1 | Исторические источники, значительная неопределённость | 1600–1749 |
| 0 | Легенда/сомнительные источники | До 1600 |

В проекте используются события с `quality_score >= 2`.

---

## 1.3 ISC Bulletin (International Seismological Centre)

**URL**: `http://www.isc.ac.uk/cgi-bin/web-db-v4`

### Формат запроса

ISC предоставляет данные через **HTTP POST-форму** или **CSV-выгрузку**. В проекте используется CSV-экспорт:

```
request=REVIEWED
out_format=CSV
bot_lat=-90
top_lat=90
left_lon=-180
right_lon=180
ctr_lat=
ctr_lon=
radius=
max_dist_units=deg
searchshape=rect
srn=
prn=
start_year=1900
start_month=01
start_day=01
start_time=00:00:00
end_year=2024
end_month=12
end_day=31
end_time=23:59:59
min_dep=
max_dep=700
min_mag=5.0
max_mag=
req_mag_type=Any
req_mag_agcy=Any
```

### Структура CSV

```csv
EVENTID,AUTHOR,DATE,TIME,LAT,LON,DEPTH,DEPFIX,AUTHOR,TYPE,MAGNITUDE
20130741,ISC,1900/01/01,00:00:00,40.000,15.000,10.0,f,ISC,MW,7.1
```

### Отличие от USGS

- ISC предоставляет **сводные** параметры очагов от нескольких агентств (ISC, PDE, BJI и др.).
- Содержит **фазовые данные** для переопределения очагов.
- Период: **1900 — настоящее время** (обновление с задержкой ~2 года).
- Приоритет: ISC > USGS при дедупликации (большее число фаз = выше точность).

---

## 1.4 GEM Active Faults + Bird (2003)

**GEM Global Active Faults**: `https://github.com/GEMScienceTools/gem-global-active-faults`
**Bird (2003) Plate Model**: `https://doi.org/10.1029/2001GC000252`

### Описание

- **GEM Active Faults** — векторная база данных активных разломов в формате GeoJSON (~15 000 сегментов).
- **Bird (2003)** — модель из 52 тектонических плит с границами в формате NUVEL/GeoJSON.

### Использование для тектонического расстояния

1. Разломы и границы плит преобразуются в **граф NetworkX** (узлы = пересечения, рёбра = сегменты разломов).
2. Вес ребра = длина сегмента в км (геодезическое расстояние).
3. Каждое сейсмическое событие **привязывается к ближайшему узлу** графа (радиус поиска: 500 км).
4. Тектоническое расстояние = кратчайший путь по графу (алгоритм Дейкстры).
5. Для **внутриплитных событий** (далее 500 км от разломов) используется фолбэк: евклидово расстояние × 1.5.

---

## 1.5 Сравнительная таблица источников

| Источник | Период | Глобальное покрытие | min_mag | Качество | Обновление |
|----------|--------|---------------------|---------|---------|-----------|
| USGS ComCat | 1900 — н.в. | Да | 2.5 | Высокое (≥1976) | Реальное время |
| NOAA NGDC | ~1600 — н.в. | Да | ~5.5 | Среднее (исторические) | Ежегодное |
| ISC Bulletin | 1900 — н.в. | Да | 3.0 | Высокое (многоагентское) | Задержка ~2 года |
| GEM Faults | — | Да | — | Геологические данные | Нерегулярное |

---

## 1.6 Процедура загрузки

```python
from fetchers.usgs import USGSFetcher
from fetchers.noaa import NOAAFetcher
from fetchers.isc import ISCFetcher
import pandas as pd
from pathlib import Path

# --- USGS ---
usgs = USGSFetcher(
    min_magnitude=5.0,
    start_year=1900,
    end_year=2024,
    chunk_years=5,          # пагинация по 5-летним окнам
    output_dir=Path("data/raw/usgs"),
    delay_between_requests=1.1,
)
usgs_catalog: pd.DataFrame = usgs.fetch_all()
# Колонки: event_id, year, month, day, lat, lon, magnitude, depth_km, mag_type, source

# --- NOAA ---
noaa = NOAAFetcher(
    min_magnitude=5.5,
    min_year=1600,
    max_year=2024,
    min_quality_score=2,
    output_path=Path("data/raw/noaa/noaa_catalog.json"),
)
noaa_catalog: pd.DataFrame = noaa.fetch_all()

# --- ISC ---
isc = ISCFetcher(
    csv_path=Path("data/raw/isc/isc_bulletin.csv"),  # предварительно загруженный файл
    min_magnitude=5.0,
)
isc_catalog: pd.DataFrame = isc.load()

print(f"USGS: {len(usgs_catalog)} событий")
print(f"NOAA: {len(noaa_catalog)} событий")
print(f"ISC:  {len(isc_catalog)} событий")
```