import pandas as pd, json, sys

df = pd.read_csv('../data/processed/unified_catalog_full.csv')
df = df[df['magnitude'] >= 6.5].copy()

major = df[df['magnitude'] >= 7.5]
minor = df[df['magnitude'] < 7.5]
minor_sample = minor.sample(min(300, len(minor)), random_state=42)
subset = pd.concat([major, minor_sample])

events = []
for _, r in subset.iterrows():
    region_col = 'region' if 'region' in df.columns else df.columns[10]
    year_val = int(r['year']) if pd.notna(r['year']) else 0
    region_val = str(r.get('region', r.get('flinn_engdahl_region', '')))[:30]
    events.append({
        'lat': round(float(r['lat']), 3),
        'lon': round(float(r['lon']), 3),
        'mag': round(float(r['magnitude']), 1),
        'year': year_val,
        'region': region_val
    })

print(f"Events: {len(events)}")
with open('events_data.json', 'w', encoding='utf-8') as f:
    json.dump(events, f, ensure_ascii=False)
print("Done: events_data.json")
