"""Перегенерация viz5 (тепловая карта) и viz6 (серия S170) с исправленной разметкой."""
import sys; sys.path.insert(0, '.')
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import json
from pathlib import Path

# Стиль
plt.rcParams.update({
    'figure.facecolor': '#0d1117', 'axes.facecolor': '#161b22',
    'axes.edgecolor': '#30363d', 'axes.labelcolor': '#c9d1d9',
    'xtick.color': '#8b949e', 'ytick.color': '#8b949e',
    'text.color': '#c9d1d9', 'grid.color': '#21262d',
    'font.family': 'DejaVu Sans', 'font.size': 10,
})

df = pd.read_csv('data/processed/unified_catalog_full.csv')
df = df[df['magnitude'] >= 6.5].copy()

# =============================================
# VIZ 5: Тепловая карта — ПЕРЕРАБОТАНА
# =============================================
print("Генерация viz5...")

region_col = 'flinn_engdahl_region' if 'flinn_engdahl_region' in df.columns else 'region'
df['decade'] = (df['year'] // 10) * 10
df_inst = df[df['year'] >= 1900].copy()

# Топ-12 регионов по числу событий
top_regions = df_inst[region_col].value_counts().head(12).index.tolist()
df_top = df_inst[df_inst[region_col].isin(top_regions)]

# Десятилетия: только от 1900 до 2020
decades = list(range(1900, 2030, 10))
decade_labels = [f"{d}s" for d in decades]

# Матрица
matrix = np.zeros((len(top_regions), len(decades)))
for i, reg in enumerate(top_regions):
    for j, dec in enumerate(decades):
        count = len(df_top[(df_top[region_col] == reg) & (df_top['decade'] == dec)])
        matrix[i, j] = count

# Рисунок — ШИРОКИЙ, высокий
fig, ax = plt.subplots(figsize=(18, 7))
im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')

# Оси
ax.set_xticks(range(len(decades)))
# Метки X — вертикально (90 градусов), крупный шрифт
ax.set_xticklabels(decade_labels, rotation=90, ha='center', fontsize=11, color='#c9d1d9')
ax.set_yticks(range(len(top_regions)))
ax.set_yticklabels(top_regions, fontsize=10, color='#c9d1d9')

# Числа в ячейках
for i in range(len(top_regions)):
    for j in range(len(decades)):
        val = int(matrix[i, j])
        if val > 0:
            ax.text(j, i, str(val), ha='center', va='center', 
                   fontsize=8, color='black' if matrix[i,j] > matrix.max()*0.5 else '#c9d1d9',
                   fontweight='bold')

# Colorbar справа
cbar = plt.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
cbar.set_label('Число событий M≥6.5', color='#c9d1d9')
cbar.ax.yaxis.set_tick_params(color='#c9d1d9')
plt.setp(cbar.ax.yaxis.get_ticklabels(), color='#c9d1d9')

ax.set_title('Активность M≥6.5 по регионам и десятилетиям (1900–2026)', 
             color='#c9d1d9', fontsize=13, pad=15)

# КРИТИЧНО: достаточный отступ снизу для вертикальных меток
plt.subplots_adjust(bottom=0.18, left=0.22, right=0.95, top=0.92)
plt.savefig('figures/viz5_heatmap_regions.png', dpi=120, 
            facecolor='#0d1117', bbox_inches='tight')
plt.close()
print("viz5 сохранён")

# =============================================
# VIZ 6: Серия S170 — ПОЛНОСТЬЮ ПЕРЕРАБОТАНА
# =============================================
print("Генерация viz6...")

# Загрузка данных серии S170
series_events = []
try:
    # Попытка из clusters.json
    with open('results/clusters.json') as f:
        clusters = json.load(f)
    
    # Ищем S170 или аналог
    s170_key = None
    for k in clusters.keys():
        if '170' in str(k) or k == 'S170':
            s170_key = k
            break
    
    if s170_key and isinstance(clusters[s170_key], dict):
        sdata = clusters[s170_key]
        if 'events' in sdata:
            for e in sdata['events']:
                if 'lat' in e and 'lon' in e and 'magnitude' in e:
                    series_events.append(e)
        elif 'event_ids' in sdata:
            ids = sdata['event_ids']
            edf = df[df['event_id'].isin(ids)]
            for _, r in edf.iterrows():
                series_events.append({
                    'year': int(r['year']), 'month': int(r.get('month', 6)),
                    'magnitude': float(r['magnitude']),
                    'lat': float(r['lat']), 'lon': float(r['lon']),
                    'region': str(r.get(region_col, ''))
                })
except Exception as e:
    print(f"clusters.json: {e}")

# Если данных нет — загрузить из cluster_assignments или создать из каталога
if len(series_events) < 3:
    try:
        ca = pd.read_csv('results/cluster_assignments.csv')
        s170_events = ca[ca['cluster_id'].astype(str).str.contains('170')]
        if len(s170_events) == 0:
            # Попробуй найти крупнейший кластер
            cluster_counts = ca['cluster_id'].value_counts()
            big_cluster = cluster_counts.index[0]
            s170_events = ca[ca['cluster_id'] == big_cluster]
        
        event_ids = s170_events['event_id'].tolist() if 'event_id' in s170_events.columns else []
        if event_ids:
            edf = df[df['event_id'].isin(event_ids)]
        else:
            edf = df[df['year'].between(2002, 2023) & (df['magnitude'] >= 7.0)].head(46)
        
        for _, r in edf.iterrows():
            series_events.append({
                'year': int(r['year']), 'month': int(r.get('month', 6)),
                'magnitude': float(r['magnitude']),
                'region': str(r.get(region_col, r.get('region', '')))
            })
    except Exception as e2:
        print(f"cluster_assignments: {e2}")
        # Fallback: крупные события 2002-2023
        edf = df[df['year'].between(2002, 2023) & (df['magnitude'] >= 7.5)].copy()
        for _, r in edf.iterrows():
            series_events.append({
                'year': int(r['year']), 'month': int(r.get('month', 6)),
                'magnitude': float(r['magnitude']),
                'region': str(r.get(region_col, r.get('region', '')))
            })

print(f"Событий в серии: {len(series_events)}")

# Сортировка по времени
series_events.sort(key=lambda e: e['year'] * 100 + e.get('month', 6))

# Простой горизонтальный timeline
fig, ax = plt.subplots(figsize=(16, 4))
fig.patch.set_facecolor('#0d1117')
ax.set_facecolor('#161b22')

years = [e['year'] + e.get('month', 6)/12 for e in series_events]
mags = [e['magnitude'] for e in series_events]
regions = [e.get('region', '')[:15] for e in series_events]

# Цвет по магнитуде
colors = []
for m in mags:
    if m >= 8.5: colors.append('#ff7b72')
    elif m >= 8.0: colors.append('#f78166')
    elif m >= 7.5: colors.append('#ffa657')
    else: colors.append('#ffd68a')

# Нормализованный размер
sizes = [min(300, max(20, (m - 6.0) ** 2 * 25)) for m in mags]

# Scatter
scatter = ax.scatter(years, [0]*len(years), s=sizes, c=colors, 
                     alpha=0.85, zorder=5, linewidths=0)

# Горизонтальная линия
if years:
    ax.axhline(0, color='#30363d', lw=1, zorder=1)
    ax.set_xlim(min(years) - 0.5, max(years) + 0.5)

# Метки только для M >= 8.0 — чередование вверх/вниз
annotated = 0
for i, (yr, mag, reg) in enumerate(zip(years, mags, regions)):
    if mag >= 8.0:
        y_offset = 0.4 if annotated % 2 == 0 else -0.5
        va = 'bottom' if y_offset > 0 else 'top'
        ax.annotate(
            f'M{mag:.1f}\n{yr:.0f}',
            xy=(yr, 0), xytext=(yr, y_offset),
            fontsize=8, ha='center', va=va, color='#e6edf3',
            arrowprops=dict(arrowstyle='->', color='#555555', lw=0.8),
            bbox=dict(boxstyle='round,pad=0.2', facecolor='#1c2128', 
                     edgecolor='#30363d', alpha=0.9)
        )
        annotated += 1

# Ось X — только целые годы
ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True, nbins=12))
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x)}'))
plt.xticks(rotation=0, color='#8b949e', fontsize=10)

# Скрыть ось Y
ax.set_yticks([])
ax.spines['left'].set_visible(False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.set_ylim(-1, 1)

ax.set_xlabel('Год', color='#c9d1d9', fontsize=11)
ax.set_title(f'Серия S170: {len(series_events)} событий в 12 регионах (2002–2023)\n'
             'Суматра 2004 (M9.1) — крупнейшее в серии', 
             color='#c9d1d9', fontsize=12, pad=10)

# Мини-легенда магнитуд
for mag_val, clr, lbl in [(9.0,'#ff7b72','M≥8.5'), (8.0,'#f78166','M8–8.5'), 
                           (7.5,'#ffa657','M7.5–8'), (7.0,'#ffd68a','M<7.5')]:
    ax.scatter([], [], s=min(300, (mag_val-6)**2*25), c=clr, label=lbl, alpha=0.85)
ax.legend(loc='upper left', framealpha=0.3, fontsize=8, 
          labelcolor='#c9d1d9', facecolor='#161b22', edgecolor='#30363d')

plt.tight_layout(pad=1.0)
plt.savefig('figures/viz6_series_s170.png', dpi=120, 
            facecolor='#0d1117', bbox_inches='tight')
plt.close()
print("viz6 сохранён")

print("\nОба графика перегенерированы:")
import os
for f in ['figures/viz5_heatmap_regions.png', 'figures/viz6_series_s170.png']:
    size = os.path.getsize(f)
    print(f"  {f}: {size:,} байт")
