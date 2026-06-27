# Скрипт полного запуска проекта paleoseismic-clustering
# Запуск: .\run_all.ps1

$PYTHON = "C:\Users\marsh\AppData\Local\Programs\Python\Python312\python.exe"
$PIP    = "C:\Users\marsh\AppData\Local\Programs\Python\Python312\Scripts\pip.exe"
$ROOT   = $PSScriptRoot

Set-Location $ROOT
Write-Host "=== Рабочая директория: $ROOT ===" -ForegroundColor Cyan

# --- 1. Установка зависимостей ---
Write-Host "`n[1/4] Установка зависимостей..." -ForegroundColor Yellow
& $PIP install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "ОШИБКА: pip install завершился с ошибкой. Проверьте requirements.txt." -ForegroundColor Red
}

# --- 2. Проверка импортов ---
Write-Host "`n[2/4] Проверка импортов..." -ForegroundColor Yellow
& $PYTHON check_imports.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK: все импорты успешны." -ForegroundColor Green
} else {
    Write-Host "ОШИБКА: некоторые импорты не удались. Подробности выше." -ForegroundColor Red
}

# --- 3. Запуск тестов ---
Write-Host "`n[3/4] Запуск тестов..." -ForegroundColor Yellow
& $PYTHON -m pytest tests/ -v --tb=short 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "OK: все тесты прошли." -ForegroundColor Green
} else {
    Write-Host "Некоторые тесты не прошли. Подробности выше." -ForegroundColor Yellow
}

# --- 4. Запуск демо кластеризации ---
Write-Host "`n[4/4] Запуск демо-скрипта..." -ForegroundColor Yellow
& $PYTHON -c @"
import sys, os
sys.path.insert(0, '.')
os.makedirs('data/processed', exist_ok=True)

import numpy as np
import pandas as pd
from src.analysis.clustering import SeismicClusterAnalyzer, _events_to_time_years
from src.analysis.monte_carlo import MonteCarloTester

rng = np.random.default_rng(42)
n = 50
df = pd.DataFrame({
    'event_id': [f'ev{i}' for i in range(n)],
    'year':  rng.integers(1900, 2024, size=n),
    'month': rng.integers(1, 13, size=n),
    'day':   rng.integers(1, 29, size=n),
    'lat':   rng.uniform(-80, 80, size=n),
    'lon':   rng.uniform(-180, 180, size=n),
    'magnitude': rng.uniform(6.5, 8.5, size=n),
    'depth_km':  rng.uniform(5, 100, size=n),
    'fe_region': rng.integers(1, 50, size=n),
})
analyzer = SeismicClusterAnalyzer()
df_nn = analyzer.find_nearest_neighbor(df)
df_cl = analyzer.identify_clusters(df_nn, eta_threshold=1e-5)
n_cl = (df_cl['cluster_id'] >= 0).sum()
print(f'Найдено кластерных событий: {n_cl}/{n}')

tester = MonteCarloTester(random_seed=42)
p = tester.pvalue(df, n_simulations=200)
print(f'p-value (200 симуляций): {p:.4f}')
print('ДЕМО ЗАВЕРШЕНО УСПЕШНО')
"@

Write-Host "`n=== Готово ===" -ForegroundColor Cyan
