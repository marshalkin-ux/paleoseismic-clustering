# 04. Справочник API

> Все публичные классы и функции проекта. Типы указаны в нотации PEP 484.

---

## fetchers/usgs.py

### class `USGSFetcher`

Загрузчик данных из USGS ComCat API с автоматической пагинацией и обработкой rate-limit.

```python
class USGSFetcher:
    def __init__(
        self,
        min_magnitude: float = 5.0,
        start_year: int = 1900,
        end_year: int = 2024,
        chunk_years: int = 5,
        output_dir: Path = Path("data/raw/usgs"),
        delay_between_requests: float = 1.1,
        max_retries: int = 3,
    ) -> None
```

**Параметры:**
- `min_magnitude` — минимальная магнитуда для запроса.
- `start_year` / `end_year` — временной диапазон.
- `chunk_years` — размер временного окна для пагинации (лет).
- `output_dir` — директория для кэширования сырых JSON-ответов.
- `delay_between_requests` — задержка между запросами (сек), рекомендуется ≥ 1.1.
- `max_retries` — число повторных попыток при HTTP-ошибках.

#### `fetch_all() -> pd.DataFrame`

Загружает полный каталог за заданный период с пагинацией.

```python
usgs = USGSFetcher(min_magnitude=6.0, start_year=1960, end_year=2024)
df: pd.DataFrame = usgs.fetch_all()
# Колонки: event_id, year, month, day, lat, lon, magnitude,
#          depth_km, mag_type_original, source_type
```

#### `fetch_chunk(start: str, end: str) -> pd.DataFrame`

Загружает один временной чанк. `start`/`end` в формате ISO8601 (`"YYYY-MM-DD"`).

#### `_parse_geojson(response: dict) -> pd.DataFrame`

Внутренний метод. Парсит GeoJSON-ответ ComCat в DataFrame.

---

## fetchers/noaa.py

### class `NOAAFetcher`

```python
class NOAAFetcher:
    def __init__(
        self,
        min_magnitude: float = 5.5,
        min_year: int = 1600,
        max_year: int = 2024,
        min_quality_score: int = 2,
        output_path: Path = Path("data/raw/noaa/noaa_catalog.json"),
    ) -> None
```

#### `fetch_all() -> pd.DataFrame`

Загружает исторический каталог NOAA NGDC. Возвращает DataFrame с теми же колонками, что `USGSFetcher.fetch_all()`, плюс `quality_score`.

#### `_map_quality_score(item: dict) -> float`

Вычисляет `quality_score` (0–4) по набору атрибутов NOAA-записи.

---

## fetchers/isc.py

### class `ISCFetcher`

```python
class ISCFetcher:
    def __init__(
        self,
        csv_path: Path,
        min_magnitude: float = 5.0,
        encoding: str = "latin-1",
    ) -> None
```

#### `load() -> pd.DataFrame`

Загружает предварительно скачанный CSV-бюллетень ISC. Выполняет очистку и приведение к стандартному формату.

---

## unifier/catalog.py

### class `CatalogUnifier`

Объединяет каталоги из нескольких источников, выполняет дедупликацию и нормализацию.

```python
class CatalogUnifier:
    def __init__(
        self,
        spatial_threshold_km: float = 50.0,
        temporal_threshold_days: float = 30.0,
        priority_order: list[str] | None = None,
    ) -> None
```

**Параметры:**
- `spatial_threshold_km` — порог пространственной близости для дедупликации.
- `temporal_threshold_days` — порог временной близости.
- `priority_order` — порядок приоритетов источников (по умолчанию `["isc", "usgs", "noaa"]`).

#### `add_catalog(df: pd.DataFrame, source: str) -> None`

Добавляет каталог в очередь объединения.

#### `unify() -> pd.DataFrame`

Выполняет объединение и дедупликацию всех добавленных каталогов.

```python
unifier = CatalogUnifier(spatial_threshold_km=50.0)
unifier.add_catalog(isc_df, source="isc")
unifier.add_catalog(usgs_df, source="usgs")
unifier.add_catalog(noaa_df, source="noaa")
unified: pd.DataFrame = unifier.unify()
```

#### `convert_magnitudes(df: pd.DataFrame) -> pd.DataFrame`

Конвертирует разные типы магнитуд к Mw по таблицам Scordilis (2006).

#### `assign_flinn_engdahl(df: pd.DataFrame) -> pd.DataFrame`

Присваивает номер региона Флинна–Энгдала каждому событию по (lat, lon).

---

## db/manager.py

### class `DBManager`

```python
class DBManager:
    def __init__(self, db_path: Path = Path("data/seismic_catalog.db")) -> None
```

#### `init_schema() -> None`

Создаёт таблицы (если не существуют) по схеме из `02_unified_format.md`.

#### `insert_events(df: pd.DataFrame) -> int`

Вставляет события из DataFrame. Возвращает число вставленных строк.

#### `query_events(min_magnitude: float = 6.5, start_year: int | None = None, end_year: int | None = None, fe_regions: list[int] | None = None) -> pd.DataFrame`

Выполняет фильтрующий запрос к таблице events.

#### `save_series(series: list[dict]) -> None`

Сохраняет найденные серии в таблицы `seismic_series` и `series_events`.

---

## analysis/completeness.py

### class `CompletenessAnalyzer`

```python
class CompletenessAnalyzer:
    def __init__(
        self,
        catalog: pd.DataFrame,
        mag_bin: float = 0.1,
        mc_correction: float = 0.2,
    ) -> None
```

#### `estimate_mc(method: str = "maxc") -> float`

Оценивает магнитуду полноты.
- `method="maxc"` — метод максимальной кривизны (Wiemer & Wyss, 2000).
- `method="gft"` — метод подгонки к закону Гутенберга–Рихтера.

**Возвращает:** `float` — оценка Mc.

#### `estimate_b_value(mc: float | None = None) -> tuple[float, float]`

MLE-оценка b-value по формуле Shi & Bolt (1982).

**Возвращает:** `(b, sigma_b)` — b-value и его стандартная ошибка.

#### `completeness_matrix(regions: list[int], epochs: list[tuple[int, int]]) -> pd.DataFrame`

Строит матрицу Mc[region, epoch].

**Параметры:**
- `regions` — список номеров FE-регионов.
- `epochs` — список пар `(start_year, end_year)`.

**Возвращает:** DataFrame с индексом по регионам и колонками по эпохам.

---

## analysis/tectonic_distance.py

### class `TectonicDistanceCalculator`

```python
class TectonicDistanceCalculator:
    def __init__(
        self,
        gem_faults_path: Path,
        bird_plates_path: Path,
        fallback_distance_km: float = 500.0,
        fallback_multiplier: float = 1.5,
        cache_path: Path | None = None,
    ) -> None
```

#### `build_graph() -> nx.Graph`

Строит граф NetworkX из файлов GEM и Bird.

#### `compute_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float`

Вычисляет тектоническое расстояние между двумя точками (км). Использует кэш если доступен.

#### `compute_distance_matrix(catalog: pd.DataFrame) -> np.ndarray`

Вычисляет полную матрицу тектонических расстояний для всех событий каталога.

**Возвращает:** массив формы `(N, N)` в км.

---

## analysis/clustering.py

### class `SeismicClusterAnalyzer`

```python
class SeismicClusterAnalyzer:
    def __init__(
        self,
        catalog: pd.DataFrame,
        distance_matrix: np.ndarray,
        b_value: float = 1.0,
        df: float = 1.6,
    ) -> None
```

#### `compute_eta_matrix() -> np.ndarray`

Вычисляет матрицу метрик ближайшего соседа η для всех пар событий (верхнетреугольная).

#### `find_nearest_parent(event_idx: int) -> tuple[int, float]`

Находит ближайшего родителя для события с индексом `event_idx`.

**Возвращает:** `(parent_idx, eta_min)`.

#### `find_global_series(eta_threshold: float, window_years: float = 1.0, step_years: float = 0.25, min_events: int = 4, min_magnitude: float = 6.5, min_fe_regions: int = 3) -> list[dict]`

Поиск глобальных серий скользящим окном (см. Методологию §3.4).

---

## analysis/montecarlo.py

### class `MonteCarloTester`

```python
class MonteCarloTester:
    def __init__(
        self,
        analyzer: SeismicClusterAnalyzer,
        n_simulations: int = 1000,
        random_seed: int | None = 42,
    ) -> None
```

#### `run(observed_series: list[dict]) -> dict`

Выполняет монте-карло тестирование.

**Возвращает:** словарь с ключами:
- `p_value: float`
- `n_observed: int`
- `null_distribution: list[int]` — число серий в каждой симуляции
- `confidence_interval: tuple[float, float]`

```python
tester = MonteCarloTester(analyzer, n_simulations=1000)
results = tester.run(observed_series=series_list)
print(f"p-value = {results['p_value']:.4f}")
```

---

## statistics.py — функции

### `gutenberg_richter_fit(magnitudes: np.ndarray, mc: float) -> tuple[float, float]`

Подгонка закона Гутенберга–Рихтера методом МНК.
**Возвращает:** `(a, b)` — параметры log10(N) = a − b·M.

### `mle_b_value(magnitudes: np.ndarray, mc: float, delta_m: float = 0.1) -> tuple[float, float]`

MLE-оценка b-value по Shi & Bolt (1982).
**Возвращает:** `(b, sigma_b)`.

### `compute_eta(t_ij: float, r_ij: float, m_i: float, b: float = 1.0, df: float = 1.6) -> float`

Вычисляет η для одной пары событий.

### `get_eta_threshold(eta_matrix: np.ndarray, percentile: float = 5.0) -> float`

Определяет порог η как percentile-й перцентиль распределения минимальных η.

---

## viz/maps.py — функции

### `plot_series_map(series: dict, catalog: pd.DataFrame, output_path: Path | None = None) -> plt.Figure`

Карта мира (Cartopy, проекция Robinson) с нанесёнными событиями серии. Размер маркеров пропорционален магнитуде; цвет — регион FE.

### `plot_completeness_map(mc_matrix: pd.DataFrame, output_path: Path | None = None) -> plt.Figure`

Карта глобальной магнитуды полноты по регионам.

## viz/dendrograms.py — функции

### `plot_eta_dendrogram(eta_matrix: np.ndarray, catalog: pd.DataFrame, output_path: Path | None = None) -> plt.Figure`

η-дендрограмма иерархической кластеризации событий (linkage = 'single', метрика = η).

## viz/completeness.py — функции

### `plot_fmd(catalog: pd.DataFrame, mc: float, b: float, output_path: Path | None = None) -> plt.Figure`

График частотно-магнитудного распределения (FMD) с нанесённой линией ГР и отметкой Mc.