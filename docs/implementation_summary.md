# Техническая документация: Реализованные улучшения

Дата: 27 июня 2026  
Версия: 2.0 (публикация в GRL)

---

## Обзор изменений

| Модуль | Что добавлено | Зачем |
|--------|--------------|-------|
| `etas_validation.py` | `etas_omori_sample()`, обновлённый `ETASCatalogGenerator` с параметрами Helmstetter & Sornette 2003, `run_false_positive_analysis` с n_observed и p-value | Оценка частоты ложных открытий; необходим для публикации в GRL |
| `multiple_testing.py` | `compute_m_eff()`, `bonferroni_holm()`, `summarize_correction_impact()` | Более строгий контроль FWER; таблица влияния поправки для рецензента |
| `declustering.py` | `find_threshold_kde()`, `plot_eta_distribution()` в классе `ZaliaipinDeclustering` | Автоматическая детекция порога η₀ без ручной настройки |
| `tectonic_distance_v2.py` | `compare_distances()`, `batch_tectonic_distances_parallel()` | Отладка и параллельное вычисление матрицы расстояний |

---

## A. ETAS-валидация (`etas_validation.py`)

### Математика

Условная интенсивность ETAS:

```
λ(t, x, y) = μ + Σ_{i: ti<t}  K · 10^{α(mi − M₀)} · (t − ti + c)^{−p} · (r² + d²)^{−q}
```

Закон Омори-Уцу (временная составляющая):

```
f(τ) = (τ + c)^{−p},   τ = t − tᵢ > 0
```

Обратная функция CDF для выборки (inverse CDF):

```
F(τ) = 1 − ((τ + c)/c)^{1−p}

τ = c · (1 − u)^{1/(1−p)} − c,   u ~ U(0, 1)
```

При p → 1 используется экспоненциальное приближение: `τ = −c · ln(u)`.

### Параметры (глобальный каталог M ≥ 6.5)

| Параметр | Значение | Источник |
|----------|---------|---------|
| μ | 0.008 | Калибровка на unified_catalog_full.csv |
| K | 0.08 | Helmstetter & Sornette (2003) |
| α | 1.0 | Helmstetter & Sornette (2003) |
| c | 0.005 дней | Ogata (1988) |
| p | 1.1 | Ogata (1988) |
| max\_trigger\_distance\_km | 500 | Ключевое ограничение: нет глобальных триггеров |
| n\_background | 80 | Типичный 50-летний каталог M≥6.5 |

**Ключевое**: `max_trigger_distance_km=500` гарантирует, что в синтетических каталогах **нет** глобальных серий по построению. Любые «серии», обнаруженные алгоритмом — ложные открытия.

### Новая функция `etas_omori_sample`

```python
from src.analysis.etas_validation import etas_omori_sample
import numpy as np

rng = np.random.default_rng(42)
times = etas_omori_sample(n=1000, c=0.005, p=1.1, t_max=365.0, rng=rng)
# → массив из 1000 значений времён [0, 365] дней
print(f"Медиана: {np.median(times):.3f} дней")   # ~0.01 дней (быстрый спад)
print(f"95-й перцентиль: {np.percentile(times, 95):.2f} дней")
```

### Пример запуска валидации

```python
from src.analysis.etas_validation import ETASCatalogGenerator
from src.analysis.clustering import SeismicClusterAnalyzer

gen = ETASCatalogGenerator(
    mu=0.008, K=0.08, alpha=1.0, c=0.005, p=1.1,
    max_trigger_distance_km=500,
)
analyzer = SeismicClusterAnalyzer()

results = gen.run_false_positive_analysis(
    cluster_analyzer=analyzer,
    n_catalogs=100,
    min_events=4,
    min_regions=3,
    time_window_years=2.0,
    n_observed=47,  # серий в реальном каталоге
    seed=42,
)

# Ожидаемый вывод:
# mean_false_series ≈ 0.1 ± 0.3
# p_value_empirical ≈ 0.000
# false_positive_rate ≈ 0.08
```

### Интерпретация результатов

| Метрика | Ожидаемое значение | Интерпретация |
|---------|-------------------|---------------|
| `mean_false_series` | < 0.5 | Среднее число ложных серий в ETAS-каталоге |
| `false_positive_rate` | < 0.15 | Доля каталогов с ≥ 1 ложной серией |
| `p_value_empirical` | < 0.001 | P(N_etas ≥ 47) ≈ 0 → результат значим |

---

## B. Коррекция на множественное тестирование (`multiple_testing.py`)

### Сравнение методов

| Метод | Контролирует | Мощность | Применение |
|-------|-------------|---------|-----------|
| Бонферрони | FWER | Низкая | Строгая верхняя граница |
| **Холм (Holm 1979)** | **FWER** | **Средняя** | **Более мощная альтернатива Бонферрони** |
| BH FDR | FDR | Высокая | Стандарт в сейсмологии |

### Метод Холма — алгоритм

```
Вход: p(1) ≤ p(2) ≤ ... ≤ p(M)

Для i = 1, ..., M:
    α_i = α / (M − i + 1)
    Если p(i) > α_i → СТОП, принять H0 для i и всех j > i
    Иначе → отклонить H0_i

Скорректированные p-value: p_adj[i] = min(1, max_{j≤i}( (M−j+1)·p[j] ))
```

### Оценка M_eff через скользящие корреляции

```python
from src.analysis.multiple_testing import compute_m_eff
import numpy as np

# Для коррелированных p-values из перекрывающихся окон:
pvals = np.array([...])   # отсортированы по времени
m_eff = compute_m_eff(pvals, window_size=50)
# m_eff < len(pvals) если есть автокорреляция

# Применить Бонферрони к m_eff независимым тестам:
from src.analysis.multiple_testing import apply_bonferroni
adj = apply_bonferroni(pvals, alpha=0.05 / len(pvals) * m_eff)
```

### Сводная таблица влияния

```python
from src.analysis.multiple_testing import summarize_correction_impact

table = summarize_correction_impact(
    series_ids=["S001", "S002", "S003", "S047"],
    raw_pvalues=np.array([0.001, 0.04, 0.06, 1e-8]),
    method="fdr_bh",
    alpha=0.05,
)
print(table[["series_id", "raw_pvalue", "adjusted_pvalue", "status"]])
# S047  1e-08  3.2e-07   survived
# S001  0.001  0.002     survived
# S002  0.040  0.053     removed_by_correction
# S003  0.060  0.060     not_significant
```

Возможные значения `status`:
- `survived` — значимо до **и** после коррекции
- `removed_by_correction` — p < α, но не после поправки
- `added_by_correction` — стало значимым только после (редко, возможно при BH)
- `not_significant` — незначимо в обоих случаях

---

## C. Zaliapin–Ben-Zion декластеризация (`declustering.py`)

### Метрика ближайшего соседа

Для пары событий j (дочернее) и i (родительское, tᵢ < tⱼ):

```
η_ij = t_ij^1 · r_ij^{df} · 10^{−b·mᵢ/2}
```

где:
- `t_ij` — временной интервал (годы)
- `r_ij` — расстояние (км)
- `df = 1.6` — фрактальная размерность сейсмичности
- `b = 1.0` — b-value

Распределение `log₁₀(η)` **бимодально**: левый пик — кластерные события, правый — фоновые.

### Автоматический порог через KDE

```python
from src.analysis.declustering import ZaliaipinDeclustering
import numpy as np

zb = ZaliaipinDeclustering(df_param=1.6, b_param=1.0)
bg, clust = zb.decluster(df)

# Получить η-значения и найти порог
etas, parents = zb._compute_eta(t_years, lats, lons, mags)
threshold = zb.find_threshold_kde(etas)
print(f"η₀ = {threshold:.4e}")   # обычно ~ 10^{-4} − 10^{-3}

# Визуализировать распределение
zb.plot_eta_distribution(
    etas, threshold,
    output_path="figures/eta_distribution.png",
)
```

Алгоритм `find_threshold_kde`:
1. KDE на `log₁₀(η)` с узкой полосой `bw=0.15` (подчёркивает бимодальность)
2. Находим все локальные минимумы `argrelmin(density, order=10)`
3. Выбираем минимум между двумя наибольшими пиками KDE

### Статистика до/после

| Метрика | GK (1974) | ZB (2013) |
|---------|-----------|-----------|
| Фоновые события | ~55% | ~45–65% |
| Кластерные | ~45% | ~35–55% |
| Параметр | T(M), R(M) | η₀ |

---

## D. Весовые коэффициенты границ плит (`tectonic_distance_v2.py`)

### Типы границ и веса

```
weight = haversine_km(A, B) × BOUNDARY_WEIGHTS[boundary_type]
```

| Тип границы | Вес | Логика |
|-------------|-----|--------|
| `subduction` | 1.0 | Максимальная передача напряжения (зоны субдукции) |
| `collision` | 1.1 | Коллизия — высокая связность (Гималаи, Загрос) |
| `transform` | 1.2 | Трансформные разломы (Сан-Андреас, Альпийский) |
| `spreading` | 1.5 | Хребты — наименее эффективная передача |

**20 сегментов**: Каскадия, Япония, Тонга, Чили, Алеутские, Суматра/Ява,
Центр.Америка, Филиппины, Марианы, Рюкю (субдукция);
Сан-Андреас, Альпийский, Карибский, Скотия (трансформ);
Северо-Атлантический, Южно-Атлантический, Индийский, Тихоокеанский (спрединг);
Гималаи, Загрос (коллизия).

### Отладка расстояний

```python
from src.analysis.tectonic_distance_v2 import TectonicDistanceV2

calc = TectonicDistanceV2()
calc.build_graph()

info = calc.compare_distances(35.0, 139.0, -33.5, -70.5)
print(info)
# {
#   'euclidean_km': 16834.2,
#   'tectonic_v1_km': 18120.5,
#   'tectonic_v2_km': 19845.3,
#   'dominant_boundary_type': 'subduction',
#   'ratio_tect_eucl': 1.18,
# }
```

### Параллельная матрица расстояний

```python
matrix = calc.batch_tectonic_distances_parallel(
    events_df,
    n_workers=4,
    max_events=200,
)
# → numpy array (n × n), симметричная
```

---

## Инструкция по запуску

### Полный конвейер

```bash
python scripts/run_full_pipeline_v2.py
```

### Только ETAS-валидация (~40 мин)

```bash
python scripts/run_etas_validation.py
# → results/etas_validation.json
```

### Сравнение методов декластеризации (~5 мин)

```bash
python scripts/run_declustering_comparison.py
# → results/declustering_comparison.json
```

### Только FDR-коррекция (~1 мин)

```bash
python scripts/apply_fdr_correction.py
# → results/fdr_corrected_series.csv
```

### Тесты (все должны быть зелёными)

```bash
python -m pytest tests/test_improvements.py -v --tb=short
```

---

## Ссылки

- Ogata, Y. (1988). Statistical models for earthquake occurrences. *JASA*, 83, 9–27.
- Helmstetter, A., & Sornette, D. (2003). Importance of direct and indirect triggered seismicity. *JGR*, 108.
- Zaliapin, I., & Ben-Zion, Y. (2013). Earthquake clusters in southern California. *JGR*, 118.
- Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate. *JRSS-B*, 57, 289–300.
- Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scand. J. Stat.*, 6, 65–70.
- Bird, P. (2003). An updated digital model of plate boundaries. *Geochem. Geophys. Geosyst.*, 4.
