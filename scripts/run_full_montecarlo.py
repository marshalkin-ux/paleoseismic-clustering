"""Полный Monte Carlo тест n=10000 с FDR коррекцией.

Использует fully-vectorized numpy (матричное вещание) на полном каталоге
M>=6.5, 1973-2026 (n=2088 событий).  Пространственная матрица r^df * m_factor
вычисляется один раз; каждая перестановка — только умножение и min по строкам.

Ожидаемое время: ~3-10 мин на современном CPU.
"""
import sys
sys.path.insert(0, '.')

import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
)
logger = logging.getLogger(__name__)

import time as time_module
import json
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

# ── Параметры ─────────────────────────────────────────────────────────────────
DF_PARAM   = 1.6      # фрактальная размерность (Baiesi-Paczuski 2004)
B_PARAM    = 0.911    # b-value из анализа полноты
N_SIM      = 10_000
SEED       = 42
MIN_MAG    = 6.5
YEAR_START = 1973
YEAR_END   = 2026

Path('results').mkdir(exist_ok=True)
Path('figures').mkdir(exist_ok=True)

# ── 1. Загрузка каталога ──────────────────────────────────────────────────────
logger.info("Загрузка каталога...")
df = pd.read_csv('data/processed/unified_catalogue.csv', low_memory=False)
df = df[
    (df['magnitude'] >= MIN_MAG) &
    (df['year'] >= YEAR_START) &
    (df['year'] <= YEAR_END)
].dropna(subset=['lat', 'lon', 'magnitude']).copy().reset_index(drop=True)

print(f"Событий M>={MIN_MAG}, {YEAR_START}-{YEAR_END}: {len(df)}")
logger.info("Каталог: %d событий", len(df))

# ── 2. Подготовка массивов, сортировка по времени ─────────────────────────────
year  = df['year'].fillna(0).astype(float).values
month = df['month'].fillna(6).astype(float).values
day   = df['day'].fillna(15).astype(float).values
times_orig = year + (month - 1) / 12.0 + (day - 1) / 365.25

order      = np.argsort(times_orig)
times_orig = times_orig[order]
lats       = df['lat'].values[order]
lons       = df['lon'].values[order]
mags       = df['magnitude'].values[order]
n          = len(times_orig)
logger.info("Событий после сортировки: %d", n)

# ── 3. Предварительное вычисление пространственной матрицы ───────────────────
logger.info("Вычисление матрицы расстояний %d×%d ...", n, n)
t0 = time_module.time()

la1 = np.radians(lats[:, None])
la2 = np.radians(lats[None, :])
lo1 = np.radians(lons[:, None])
lo2 = np.radians(lons[None, :])
dlat = la2 - la1
dlon = lo2 - lo1
a = np.sin(dlat / 2)**2 + np.cos(la1) * np.cos(la2) * np.sin(dlon / 2)**2
r_mat = 2 * 6371.0 * np.arcsin(np.sqrt(np.clip(a, 0, 1))) * 1.5   # км × поправка

logger.info("Матрица расстояний вычислена за %.1f с", time_module.time() - t0)

# spatial_factor[i,j] = r[i,j]^df * 10^(-b*m[i])
# Это фиксированная часть eta; меняется только dt при перестановке.
with np.errstate(divide='ignore', invalid='ignore'):
    r_df = r_mat ** DF_PARAM
r_df[r_mat == 0] = np.inf                          # нулевые расстояния → ∞

mag_factor     = 10 ** (-B_PARAM * mags)            # shape (n,)
spatial_factor = r_df * mag_factor[:, None]          # shape (n, n)  — ФИКСИРОВАНО

# Буферы — выделяем один раз, переиспользуем во всех симуляциях
dt_buf       = np.empty((n, n), dtype=np.float64)
eta_buf      = np.empty((n, n), dtype=np.float64)
nn_eta_buf   = np.empty(n,      dtype=np.float64)

logger.info(
    "Выделено памяти: 3 матрицы %.0f MB + spatial_factor %.0f MB",
    3 * n * n * 8 / 1e6,
    n * n * 8 / 1e6,
)


def mean_log_eta_fast(times: np.ndarray) -> float:
    """Векторизованное среднее log10(eta_nn).

    Параметры пространства фиксированы в spatial_factor.
    Только dt меняется при перестановке.
    """
    # dt_buf[i,j] = times[j] - times[i]
    np.subtract(times[None, :], times[:, None], out=dt_buf)
    # eta_buf[i,j] = dt * spatial_factor   (∞ где dt<=0)
    np.multiply(dt_buf, spatial_factor, out=eta_buf)
    eta_buf[dt_buf <= 0] = np.inf
    # Ближайший сосед j = argmin_i eta[i,j]
    np.nanmin(eta_buf, axis=0, out=nn_eta_buf)     # min по строкам → shape (n,)
    valid = nn_eta_buf[np.isfinite(nn_eta_buf) & (nn_eta_buf > 0)]
    return float(np.mean(np.log10(valid))) if len(valid) > 0 else 0.0


# ── 4. Наблюдаемая статистика ─────────────────────────────────────────────────
logger.info("Вычисление наблюдаемой статистики...")
observed_stat = mean_log_eta_fast(times_orig)
logger.info("Observed mean log10(eta) = %.4f", observed_stat)
print(f"Наблюдаемая статистика: {observed_stat:.4f}")

# ── 5. Monte Carlo перестановочный тест ───────────────────────────────────────
rng             = np.random.default_rng(SEED)
null_dist       = np.empty(N_SIM, dtype=np.float64)
t_mc_start      = time_module.time()
perm_times      = np.empty(n, dtype=np.float64)   # буфер для перестановки

logger.info("Старт %d перестановок...", N_SIM)

for s in range(N_SIM):
    # Перемешиваем метки времени, позиции и магнитуды фиксированы
    np.copyto(perm_times, rng.permutation(times_orig))
    null_dist[s] = mean_log_eta_fast(perm_times)

    if (s + 1) % 500 == 0:
        elapsed   = time_module.time() - t_mc_start
        rate      = (s + 1) / elapsed
        eta_sec   = (N_SIM - s - 1) / max(rate, 1e-9)
        p_current = float(np.mean(null_dist[:s+1] <= observed_stat))
        logger.info(
            "  %d/%d | %.1f сим/с | ETA %.1f мин | p_current=%.4f",
            s + 1, N_SIM, rate, eta_sec / 60, p_current,
        )
        print(f"  {s+1:5d}/{N_SIM} | p_current={p_current:.4f} | ETA {eta_sec/60:.1f} мин")

elapsed_total = time_module.time() - t_mc_start
logger.info("Monte Carlo завершён за %.1f с (%.2f мин)", elapsed_total, elapsed_total / 60)

# ── 6. Итоговые статистики ────────────────────────────────────────────────────
valid_sim = null_dist[np.isfinite(null_dist)]
n_extreme = int(np.sum(valid_sim <= observed_stat))
# Discrete permutation p-value: (k+1)/(n+1), k = count of nulls as extreme as observed
p_value = float((n_extreme + 1) / (len(valid_sim) + 1))
null_mean = float(np.mean(valid_sim))
null_std  = float(np.std(valid_sim, ddof=1))
z_score   = float((observed_stat - null_mean) / (null_std + 1e-30))

print(f"\n{'='*50}")
print(f"=== РЕЗУЛЬТАТЫ MONTE CARLO (n={N_SIM:,}) ===")
print(f"{'='*50}")
print(f"Событий в каталоге:            {n}")
print(f"Наблюдаемое mean log10(eta):   {observed_stat:.4f}")
print(f"Нулевое: mean={null_mean:.4f}, std={null_std:.4f}")
print(f"p-value:                       {p_value:.6f}  ({n_extreme + 1}/{len(valid_sim) + 1} permutations)")
print(f"z-score:                       {z_score:.2f}")
print(f"Время расчёта:                 {elapsed_total/60:.1f} мин")

if p_value < 0.001:
    interp = "ВЫСОКОЗНАЧИМО: p < 0.001"
elif p_value < 0.01:
    interp = "ЗНАЧИМО: p < 0.01"
elif p_value < 0.05:
    interp = "УМЕРЕННО ЗНАЧИМО: 0.01 <= p < 0.05"
elif p_value < 0.10:
    interp = "МАРГИНАЛЬНО ЗНАЧИМО: 0.05 <= p < 0.10"
else:
    interp = "НЕ ЗНАЧИМО: p >= 0.10"

print(f"Интерпретация:                 {interp}")

# ── 7. FDR коррекция (если есть p-value по сериям) ────────────────────────────
n_sig_fdr = 0
try:
    from src.analysis.multiple_testing import apply_fdr_bh
    cluster_summary = pd.read_csv('results/cluster_summary.csv')
    if 'pvalue' in cluster_summary.columns:
        reject, adj_p = apply_fdr_bh(cluster_summary['pvalue'].values)
        cluster_summary['adjusted_pvalue'] = adj_p
        cluster_summary['significant_fdr'] = reject
        n_sig_fdr = int(reject.sum())
        print(f"\nFDR BH коррекция: {n_sig_fdr} серий значимы при FDR=0.05")
        cluster_summary.to_csv('results/cluster_summary_fdr.csv', index=False)
    else:
        print("\nFDR: колонка 'pvalue' отсутствует в cluster_summary.csv — пропущено")
except Exception as exc:
    print(f"FDR: {exc}")

# ── 8. Сохранение результатов ─────────────────────────────────────────────────
mc_results = {
    'n_simulations':            N_SIM,
    'n_events':                 int(n),
    'df_param':                 DF_PARAM,
    'b_param':                  B_PARAM,
    'observed_statistic':       observed_stat,
    'null_mean':                null_mean,
    'null_std':                 null_std,
    'n_extreme_nulls':          n_extreme,
    'p_value':                  p_value,
    'p_value_formula':          '(k+1)/(n+1)',
    'z_score':                  z_score,
    'significant_global':       p_value < 0.01,
    'significant_marginal':     p_value < 0.10,
    'n_significant_series_fdr': n_sig_fdr,
    'interpretation':           interp,
    'elapsed_minutes':          round(elapsed_total / 60, 2),
    'timestamp':                datetime.now().isoformat(),
}
with open('results/montecarlo_full.json', 'w') as fh:
    json.dump(mc_results, fh, indent=2)

np.save('results/null_distribution.npy', null_dist)
print("\nСохранено: results/montecarlo_full.json")
print("Сохранено: results/null_distribution.npy")

# ── 9. Обновление analysis_summary.json ───────────────────────────────────────
try:
    with open('results/analysis_summary.json') as fh:
        summary = json.load(fh)
    summary['monte_carlo'] = {
        'n_simulations':       N_SIM,
        'p_value':             p_value,
        'z_score':             z_score,
        'observed_mean_log_eta': observed_stat,
        'interpretation':      interp,
    }
    with open('results/analysis_summary.json', 'w') as fh:
        json.dump(summary, fh, indent=2)
    print("Обновлено:  results/analysis_summary.json")
except Exception as exc:
    logger.warning("analysis_summary update: %s", exc)

# ── 10. Рисунок ───────────────────────────────────────────────────────────────
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(10, 6))
ax.hist(null_dist, bins=80, color='steelblue', alpha=0.75,
        label='Нулевое распределение')
ax.axvline(observed_stat, color='red', lw=2.5,
           label=f'Наблюдаемое = {observed_stat:.3f}')
ax.axvline(np.percentile(null_dist, 1), color='darkorange', ls='--', lw=1.5,
           label=f'1-й перцентиль = {np.percentile(null_dist, 1):.3f}')
ax.axvline(np.percentile(null_dist, 5), color='gold', ls=':', lw=1.5,
           label=f'5-й перцентиль = {np.percentile(null_dist, 5):.3f}')
ax.set_xlabel(r'Среднее $\log_{10}(\eta)$ ближайшего соседа', fontsize=12)
ax.set_ylabel('Частота', fontsize=12)
ax.set_title(
    f'Monte Carlo тест (n = {N_SIM:,} перестановок, {n} событий)\n'
    f'p-value = {p_value:.4f},  z = {z_score:.2f}',
    fontsize=13,
)
ax.legend(fontsize=10)
ax.text(0.02, 0.97, interp, transform=ax.transAxes,
        fontsize=10, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
plt.tight_layout()
fig_path = 'figures/montecarlo_full_n10000.png'
plt.savefig(fig_path, dpi=300, bbox_inches='tight')
plt.close()
print(f"Рисунок: {fig_path}")
print("\nГОТОВО.")
