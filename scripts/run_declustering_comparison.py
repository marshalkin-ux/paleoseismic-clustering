"""Compares Gardner-Knopoff and Zaliapin-Ben-Zion declustering."""
import sys; sys.path.insert(0, '.')
import pandas as pd
from pathlib import Path
from src.analysis.declustering import GardnerKnopoffDeclustering, ZaliaipinDeclustering

catalog_path = None
for p in ['data/processed/unified_catalog_full.csv', 'data/processed/unified_catalog.csv']:
    if Path(p).exists():
        catalog_path = p
        break

if catalog_path is None:
    print("Catalog not found!")
    exit(1)

df = pd.read_csv(catalog_path)
print(f"Catalog: {len(df)} events")
print(f"Columns: {df.columns.tolist()}")

if 'year' in df.columns:
    df = df[df['year'] >= 1973].copy()
    print(f"After filter (1973+): {len(df)} events")

# Gardner-Knopoff
gk = GardnerKnopoffDeclustering()
gk_mainshocks, gk_aftershocks = gk.decluster(df)
n_gk = len(gk_mainshocks)
total = len(df)
print(f"\nGardner-Knopoff: {n_gk} independent of {total} ({100*n_gk/total:.1f}%)")

# Zaliapin-Ben-Zion
zbz = ZaliaipinDeclustering()
zbz_mainshocks, zbz_aftershocks = zbz.decluster(df)
n_zbz = len(zbz_mainshocks)
print(f"Zaliapin-Ben-Zion: {n_zbz} independent of {total} ({100*n_zbz/total:.1f}%)")

diff = n_gk - n_zbz
direction = "more" if diff > 0 else "less"
print(f"\nDifference: GK removes {abs(diff)} events {direction} than ZBZ")
print(f"GK independent rate: {100*n_gk/total:.1f}%")
print(f"ZBZ independent rate: {100*n_zbz/total:.1f}%")
