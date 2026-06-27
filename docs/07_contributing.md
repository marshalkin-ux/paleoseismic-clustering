# 07. Участие в разработке

---

## 7.1 Запуск тестов

Тесты написаны с использованием **pytest**. Минимальное покрытие для PR: **80%**.

```bash
# Запуск всех тестов
python -m pytest tests/

# С покрытием
python -m pytest tests/ --cov=. --cov-report=html --cov-report=term-missing

# Только конкретный модуль
python -m pytest tests/test_completeness.py -v

# Быстрый запуск (без медленных интеграционных тестов)
python -m pytest tests/ -m "not slow" -v
```

### Структура тестов

```
tests/
├── conftest.py               # фикстуры: мини-каталог, граф разломов-заглушка
├── test_usgs_fetcher.py      # юнит-тесты USGSFetcher (мок HTTP)
├── test_noaa_fetcher.py
├── test_isc_fetcher.py
├── test_catalog_unifier.py   # тесты дедупликации
├── test_completeness.py      # тесты Mc и b-value
├── test_tectonic_distance.py # тесты графа и Дейкстры
├── test_clustering.py        # тесты η-матрицы и поиска серий
├── test_montecarlo.py
└── integration/
    ├── test_full_pipeline.py # @pytest.mark.slow
    └── test_db_manager.py
```

### Маркеры pytest

| Маркер | Описание |
|--------|---------|
| `@pytest.mark.slow` | Тест > 30 сек (интеграционный) |
| `@pytest.mark.network` | Требует сетевого доступа |
| `@pytest.mark.gpu` | Требует GPU (не используется в текущей версии) |

---

## 7.2 Добавление нового источника данных

Для добавления нового сейсмического каталога (например, EMSC или JMA) следуйте этой структуре:

### Шаг 1: Создать класс fetcher

Создайте файл `fetchers/новый_источник.py`, реализовав интерфейс `BaseFetcher`:

```python
from fetchers.base import BaseFetcher
import pandas as pd
from pathlib import Path


class MyNewFetcher(BaseFetcher):
    """
    Загрузчик данных из MyNew каталога.

    Параметры
    ----------
    min_magnitude : float
        Минимальная магнитуда.
    output_dir : Path
        Директория для кэша.
    """

    SOURCE_NAME = "mynew"
    BASE_URL = "https://api.mynewcatalog.org/events"

    def __init__(
        self,
        min_magnitude: float = 5.0,
        output_dir: Path = Path("data/raw/mynew"),
    ) -> None:
        super().__init__(min_magnitude=min_magnitude, output_dir=output_dir)

    def fetch_all(self) -> pd.DataFrame:
        """Загружает полный каталог."""
        # ... реализация ...
        raise NotImplementedError

    def _normalize(self, raw: dict) -> pd.DataFrame:
        """
        Приводит сырые данные к стандартным колонкам:
        event_id, year, month, day, lat, lon, magnitude,
        depth_km, mag_type_original, source_type, quality_score
        """
        # ... реализация ...
        raise NotImplementedError
```

### Шаг 2: Добавить в CatalogUnifier

В `unifier/catalog.py` добавить `"mynew"` в список допустимых source_type:

```python
VALID_SOURCES = {"usgs", "noaa", "isc", "mynew"}
```

### Шаг 3: Написать тесты

Создать `tests/test_mynew_fetcher.py` с минимум:
- тест `fetch_all()` на мок-ответе
- тест `_normalize()` на примере одной записи
- тест обработки HTTP-ошибок

### Шаг 4: Обновить документацию

- Добавить описание источника в `docs/01_data_sources.md`.
- Обновить сравнительную таблицу.
- Добавить класс в `docs/04_api_reference.md`.

---

## 7.3 Кодстайл

### PEP 8

Проект следует [PEP 8](https://peps.python.org/pep-0008/). Автоматическая проверка через **flake8** и форматирование через **black**:

```bash
# Проверка
flake8 . --max-line-length=100 --exclude=.venv,build

# Форматирование
black . --line-length=100

# Сортировка импортов
isort . --profile=black
```

Конфигурация в `pyproject.toml`:

```toml
[tool.black]
line-length = 100
target-version = ["py310", "py311"]

[tool.isort]
profile = "black"
line_length = 100

[tool.flake8]
max-line-length = 100
extend-ignore = ["E203", "W503"]
```

### Docstrings

Все публичные классы, методы и функции обязаны иметь docstrings в формате **NumPy**:

```python
def estimate_mc(self, method: str = "maxc") -> float:
    """
    Оценивает магнитуду полноты каталога.

    Параметры
    ----------
    method : str
        Метод оценки: 'maxc' (максимальная кривизна) или 'gft' (подгонка ГР).

    Возвращает
    ----------
    float
        Оценка магнитуды полноты Mc.

    Исключения
    ----------
    ValueError
        Если method не является допустимым значением.

    Примеры
    --------
    >>> analyzer = CompletenessAnalyzer(catalog)
    >>> mc = analyzer.estimate_mc(method='maxc')
    >>> print(f"Mc = {mc:.1f}")
    Mc = 5.2
    """
```

**Язык docstrings**: русский (описания, параметры, примеры).

### Type hints

Type hints **обязательны** для всех публичных методов и функций. Используйте `from __future__ import annotations` для совместимости с Python 3.10.

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
    import pandas as pd


def compute_eta(
    t_ij: float,
    r_ij: float,
    m_i: float,
    b: float = 1.0,
    df: float = 1.6,
) -> float:
    ...
```

---

## 7.4 Git Flow

Проект использует упрощённый **Git Flow**:

```
main          ← стабильные релизы (тегируются: v1.0.0)
  └── develop ← текущая разработка
        ├── feature/tectonic-distance-cache
        ├── feature/noaa-quality-score
        └── fix/dedup-edge-case
```

### Правила ветвления

| Ветка | Назначение | Merge в |
|-------|-----------|---------|
| `main` | Релизы; защищена | — |
| `develop` | Актуальная разработка | `main` (через PR) |
| `feature/*` | Новый функционал | `develop` |
| `fix/*` | Исправления багов | `develop` (hotfix: `main`) |
| `docs/*` | Только документация | `develop` |
| `refactor/*` | Рефакторинг без изменения функциональности | `develop` |

### Соглашения о коммитах (Conventional Commits)

```
feat: добавить поддержку EMSC-каталога
fix: исправить переполнение при вычислении eta для t_ij=0
docs: обновить quickstart — установка Cartopy на Windows
refactor: оптимизировать compute_distance_matrix через векторизацию
test: добавить тесты для граничных случаев дедупликации
chore: обновить зависимости (networkx 3.2 -> 3.3)
```

---

## 7.5 Чеклист для Pull Request

Перед открытием PR убедитесь, что выполнены все пункты:

### Код

- [ ] Код соответствует PEP 8 (проверен `flake8`)
- [ ] Код отформатирован (`black`, `isort`)
- [ ] Все публичные методы имеют type hints
- [ ] Все публичные методы имеют docstrings на русском
- [ ] Нет закомментированного кода или отладочных `print()`

### Тесты

- [ ] Написаны тесты для новой функциональности
- [ ] Все тесты проходят: `python -m pytest tests/`
- [ ] Покрытие не ниже 80%: `pytest --cov=. --cov-fail-under=80`

### Документация

- [ ] Обновлён соответствующий раздел в `docs/`
- [ ] Если добавлен новый класс/функция — обновлён `docs/04_api_reference.md`
- [ ] Если изменена методология — обновлён `docs/03_methodology.md`

### Git

- [ ] Ветка создана от актуального `develop` (`git fetch && git rebase origin/develop`)
- [ ] Коммиты следуют Conventional Commits
- [ ] PR нацелен на `develop`, не на `main`
- [ ] В описании PR указаны: что изменено, зачем, как проверить

### Опционально

- [ ] Добавлена запись в `CHANGELOG.md`
- [ ] Обновлена версия в `pyproject.toml` (при значимых изменениях)