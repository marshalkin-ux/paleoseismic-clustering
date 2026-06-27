"""Загрузка и объединение полного каталога: 1900-2026 USGS + все NOAA.

Шаг 1: Загрузить дополнительные страницы NOAA (912 CE – 1972).
Шаг 2: Прочитать все USGS JSON (1900-2026) с диска.
Шаг 3: Объединить и сохранить unified_catalog_full.csv.
"""
import sys
sys.path.insert(0, '.')

import json
import logging
import time
from pathlib import Path

import pandas as pd
import numpy as np
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s  %(levelname)-8s  %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)

NOAA_URL = "https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/earthquakes"
RAW_NOAA = Path('data/raw/noaa')
RAW_USGS = Path('data/raw/usgs')
PROCESSED = Path('data/processed')
PROCESSED.mkdir(parents=True, exist_ok=True)

# ─── Шаг 1: Докачать NOAA (все страницы, которых ещё нет) ────────────────────

def fetch_noaa_all_pages(min_magnitude: float = 6.0) -> list[dict]:
    """Скачивает все страницы NOAA NGDC каталога."""
    all_items: list[dict] = []
    page = 1
    page_size = 1000

    # Загружаем уже скачанные страницы
    existing_pages = sorted(RAW_NOAA.glob('noaa_page*.json'))
    already_fetched = set(int(p.stem.replace('noaa_page', '')) for p in existing_pages)
    logger.info("Уже скачано страниц NOAA: %d", len(already_fetched))

    # Сначала загружаем из кэша
    for p in existing_pages:
        all_items.extend(json.loads(p.read_text(encoding='utf-8')))

    # Продолжаем с первой отсутствующей страницы
    page = max(already_fetched) + 1 if already_fetched else 1

    while True:
        if page in already_fetched:
            page += 1
            continue

        params = {
            'minMagnitude': min_magnitude,
            'pageNumber': page,
            'pageSize': page_size,
        }
        try:
            resp = requests.get(NOAA_URL, params=params, timeout=60)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            logger.warning("NOAA страница %d — ошибка: %s", page, exc)
            # Три попытки с паузой
            for attempt in range(2):
                time.sleep(3 * (attempt + 1))
                try:
                    resp = requests.get(NOAA_URL, params=params, timeout=60)
                    resp.raise_for_status()
                    data = resp.json()
                    break
                except Exception:
                    pass
            else:
                logger.error("Страница %d — все попытки исчерпаны, прекращаем.", page)
                break

        items = data.get('items', [])
        if not items:
            logger.info("NOAA: страница %d пустая, загрузка завершена.", page)
            break

        fpath = RAW_NOAA / f'noaa_page{page:04d}.json'
        fpath.write_text(json.dumps(items, ensure_ascii=False), encoding='utf-8')
        all_items.extend(items)
        logger.info("NOAA страница %d: %d событий (всего %d)", page, len(items), len(all_items))

        if len(items) < page_size:
            break
        page += 1
        time.sleep(0.3)  # вежливая пауза

    return all_items


def noaa_items_to_df(items: list[dict]) -> pd.DataFrame:
    """Конвертирует NOAA items в унифицированный DataFrame."""
    COLS = [
        'event_id', 'year', 'year_error', 'month', 'day',
        'lat', 'lon', 'magnitude', 'magnitude_error', 'depth_km',
        'region', 'source_type', 'reference', 'quality_score',
    ]
    rows = []
    for item in items:
        year_raw = item.get('year')
        if year_raw is None:
            continue
        year = int(year_raw)

        if year < 0:
            year_error, quality, src_type = 50, 0.3, 'paleoseismic'
        elif year < 1000:
            year_error, quality, src_type = 20, 0.4, 'historical'
        elif year < 1900:
            year_error, quality, src_type = 10, 0.6, 'historical'
        else:
            year_error, quality, src_type = 1, 0.9, 'instrumental'

        mag_raw = item.get('eqMagnitude')
        mag = float(mag_raw) if mag_raw is not None else None

        rows.append({
            'event_id': f"noaa_{item.get('id', '')}",
            'year': year,
            'year_error': year_error,
            'month': item.get('month'),
            'day': item.get('day'),
            'lat': item.get('latitude'),
            'lon': item.get('longitude'),
            'magnitude': mag,
            'magnitude_error': None,
            'depth_km': item.get('focal_depth'),
            'region': item.get('locationName', ''),
            'source_type': src_type,
            'reference': 'NOAA NGDC',
            'quality_score': quality,
        })
    return pd.DataFrame(rows, columns=COLS)


# ─── Шаг 2: Прочитать все USGS JSON (1900-2026) ──────────────────────────────

def load_usgs_all() -> pd.DataFrame:
    """Загружает все USGS JSON-файлы с диска (1900-2026)."""
    COLS = [
        'event_id', 'year', 'year_error', 'month', 'day',
        'lat', 'lon', 'magnitude', 'magnitude_error', 'depth_km',
        'region', 'source_type', 'reference', 'quality_score',
    ]
    files = sorted(RAW_USGS.glob('usgs_*.json'))
    logger.info("USGS файлов на диске: %d", len(files))

    records = []
    for f in files:
        data = json.loads(f.read_text(encoding='utf-8'))
        records.extend(data.get('features', []))

    logger.info("USGS событий до обработки: %d", len(records))

    rows = []
    for feat in records:
        props = feat.get('properties', {})
        geom = feat.get('geometry', {})
        coords = geom.get('coordinates', [None, None, None])
        time_ms = props.get('time')
        if time_ms is None:
            continue
        dt = pd.to_datetime(time_ms, unit='ms', utc=True)
        rows.append({
            'event_id': feat.get('id', ''),
            'year': int(dt.year),
            'year_error': 0,
            'month': int(dt.month),
            'day': int(dt.day),
            'lat': coords[1],
            'lon': coords[0],
            'magnitude': props.get('mag'),
            'magnitude_error': props.get('magError'),
            'depth_km': coords[2],
            'region': props.get('place', ''),
            'source_type': 'instrumental',
            'reference': 'USGS ComCat',
            'quality_score': 0.95 if props.get('status') == 'reviewed' else 0.80,
        })

    df = pd.DataFrame(rows, columns=COLS)
    logger.info("USGS DataFrame: %d строк, %d – %d годы", len(df), df['year'].min(), df['year'].max())
    return df


# ─── Шаг 3: Объединение ───────────────────────────────────────────────────────

def assign_fe_region(df: pd.DataFrame) -> pd.DataFrame:
    """Назначает регион Flinn-Engdahl по ближайшему центру."""
    from scipy.spatial import cKDTree
    import numpy as np

    FE_REGIONS = [
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

    fe_coords = np.array([(r[2], r[3]) for r in FE_REGIONS])
    fe_tree = cKDTree(fe_coords)

    coords = df[['lat', 'lon']].fillna(0).values
    _, idxs = fe_tree.query(coords)
    df = df.copy()
    df['fe_region'] = [FE_REGIONS[i][0] for i in idxs]

    # Обновляем пустые имена регионов
    fe_names = [FE_REGIONS[i][1] for i in idxs]
    mask = df['region'].isna() | (df['region'] == '')
    df.loc[mask, 'region'] = [fe_names[i] for i, m in enumerate(mask) if m]
    return df


def deduplicate(df: pd.DataFrame, spatial_km: float = 50.0, time_days: float = 30.0) -> pd.DataFrame:
    """Убирает дублирующие события: одно и то же в 50 км / 30 дней."""
    from scipy.spatial import cKDTree
    import numpy as np

    SOURCE_PRIORITY = {'ISC Bulletin': 3, 'USGS ComCat': 2, 'NOAA NGDC': 1}
    df = df.copy()
    df['_priority'] = df['reference'].map(SOURCE_PRIORITY).fillna(0)
    df = df.sort_values('_priority', ascending=False).reset_index(drop=True)
    df = df.dropna(subset=['lat', 'lon', 'year'])

    lat_rad = np.radians(df['lat'].values)
    lon_rad = np.radians(df['lon'].values)
    r_earth = 6371.0
    threshold_rad = spatial_km / r_earth

    coords = np.column_stack([lat_rad, lon_rad])
    tree = cKDTree(coords)

    year = df['year'].fillna(0).astype(float).values
    month = df['month'].fillna(6).astype(float).values
    day = df['day'].fillna(15).astype(float).values
    days_epoch = year * 365.25 + (month - 1) * 30.44 + day

    kept = np.ones(len(df), dtype=bool)
    for i in range(len(df)):
        if not kept[i]:
            continue
        neighbors = tree.query_ball_point(coords[i], r=threshold_rad * 1.5)
        for j in neighbors:
            if j <= i or not kept[j]:
                continue
            if abs(days_epoch[i] - days_epoch[j]) <= time_days:
                kept[j] = False

    result = df[kept].drop(columns=['_priority'], errors='ignore').copy()
    logger.info("Дедупликация: %d → %d событий", len(df), len(result))
    return result.reset_index(drop=True)


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("ШАГ 1: Загрузка всех страниц NOAA NGDC")
    logger.info("=" * 60)
    noaa_items = fetch_noaa_all_pages(min_magnitude=6.0)
    df_noaa = noaa_items_to_df(noaa_items)
    logger.info("NOAA итого: %d событий, %d – %d годы",
                len(df_noaa), df_noaa['year'].min(), df_noaa['year'].max())

    logger.info("=" * 60)
    logger.info("ШАГ 2: Загрузка USGS 1900-2026 с диска")
    logger.info("=" * 60)
    df_usgs = load_usgs_all()

    logger.info("=" * 60)
    logger.info("ШАГ 3: Объединение каталогов")
    logger.info("=" * 60)
    df_all = pd.concat([df_usgs, df_noaa], ignore_index=True)
    logger.info("До дедупликации: %d событий", len(df_all))

    df_all = deduplicate(df_all)
    df_all = assign_fe_region(df_all)

    # Статистика по эпохам
    print("\n=== СТАТИСТИКА ПОЛНОГО КАТАЛОГА ===")
    print(f"Всего событий: {len(df_all)}")
    print(f"Период: {df_all['year'].min()} – {df_all['year'].max()}")
    for label, mask in [
        ('BCE (до 0)', df_all['year'] < 0),
        ('1–1900',     (df_all['year'] >= 1) & (df_all['year'] < 1900)),
        ('1900–1972',  (df_all['year'] >= 1900) & (df_all['year'] < 1973)),
        ('1973–2026',  df_all['year'] >= 1973),
    ]:
        n = mask.sum()
        sub = df_all[mask]
        has_mag = sub['magnitude'].notna().sum()
        print(f"  {label}: {n} событий ({has_mag} с магнитудой)")

    print(f"\nКачество (quality_score):\n{df_all['quality_score'].describe()}")

    outpath = PROCESSED / 'unified_catalog_full.csv'
    df_all.to_csv(outpath, index=False, encoding='utf-8')
    logger.info("Сохранено: %s (%d строк)", outpath, len(df_all))
    print(f"\nСохранено: {outpath}")
