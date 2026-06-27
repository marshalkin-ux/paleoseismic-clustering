"""Поиск экстремальных значений в найденных сейсмических сериях."""
import sys; sys.path.insert(0, '.')
import pandas as pd
import numpy as np
import json
from math import radians, sin, cos, sqrt, atan2

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1-a))

# Загрузка каталога
df = pd.read_csv('data/processed/unified_catalog.csv')
df = df[df['magnitude'] >= 6.5].copy()

# Загрузка кластеров
try:
    summary = pd.read_csv('results/cluster_summary.csv')
    print("Колонки summary:", summary.columns.tolist())
    print(summary.head())
except Exception as e:
    print(f"Summary error: {e}")
    summary = None

try:
    with open('results/clusters.json') as f:
        clusters = json.load(f)
    print(f"Кластеров в JSON: {len(clusters)}")
    # Показать структуру первого кластера
    first_key = list(clusters.keys())[0]
    print(f"Пример кластера {first_key}:", str(clusters[first_key])[:500])
except Exception as e:
    print(f"Clusters JSON error: {e}")
    clusters = {}

# Попытка найти экстремальные серии
extremes = {}

if summary is not None and len(summary) > 0:
    print("\n=== ЭКСТРЕМАЛЬНЫЕ СЕРИИ ===")
    
    # Найди колонки с нужными данными
    cols = summary.columns.tolist()
    print("Доступные колонки:", cols)
    
    # Самая большая (по числу событий)
    if 'n_events' in cols or 'size' in cols:
        size_col = 'n_events' if 'n_events' in cols else 'size'
        biggest = summary.nlargest(1, size_col).iloc[0]
        print(f"\nСамая большая: {biggest.to_dict()}")
        extremes['biggest'] = biggest.to_dict()
    
    # Самая долгая по времени
    if 'duration_days' in cols:
        longest = summary.nlargest(1, 'duration_days').iloc[0]
        print(f"\nСамая долгая: {longest.to_dict()}")
        extremes['longest'] = longest.to_dict()
    
    # Наибольший охват регионов
    if 'n_regions' in cols:
        widest = summary.nlargest(1, 'n_regions').iloc[0]
        print(f"\nНаибольший охват: {widest.to_dict()}")
        extremes['widest'] = widest.to_dict()
    
    # Наибольшая магнитуда
    if 'max_magnitude' in cols:
        strongest = summary.nlargest(1, 'max_magnitude').iloc[0]
        print(f"\nСильнейшее событие: {strongest.to_dict()}")
        extremes['strongest'] = strongest.to_dict()

# Попытка вычислить географическое расстояние по кластерам
if clusters:
    max_dist = 0
    max_dist_series = None
    
    for sid, sdata in clusters.items():
        if not isinstance(sdata, dict):
            continue
        
        # Попытаться найти координаты событий серии
        events_in_series = None
        if 'events' in sdata:
            events_in_series = sdata['events']
        elif 'event_ids' in sdata:
            ids = sdata['event_ids']
            events_in_series = df[df['event_id'].isin(ids)][['lat','lon','magnitude','year']].to_dict('records')
        
        if not events_in_series or len(events_in_series) < 2:
            continue
            
        # Вычислить максимальное расстояние между событиями серии
        try:
            coords = [(e['lat'], e['lon']) for e in events_in_series if 'lat' in e and 'lon' in e]
            if len(coords) < 2:
                continue
            
            series_max = 0
            for i in range(len(coords)):
                for j in range(i+1, len(coords)):
                    d = haversine(coords[i][0], coords[i][1], coords[j][0], coords[j][1])
                    series_max = max(series_max, d)
            
            if series_max > max_dist:
                max_dist = series_max
                max_dist_series = sid
        except:
            continue
    
    if max_dist_series:
        print(f"\nСамая протяжённая серия: {max_dist_series}, расстояние {max_dist:.0f} км")
        extremes['most_extensive'] = {'series_id': max_dist_series, 'distance_km': round(max_dist)}

print("\n=== ИТОГ ===")
print(json.dumps(extremes, default=str, indent=2, ensure_ascii=False))

# Сохранить
with open('results/extremes.json', 'w', encoding='utf-8') as f:
    json.dump(extremes, f, default=str, indent=2, ensure_ascii=False)
