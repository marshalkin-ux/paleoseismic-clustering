# Paleoseismic Clustering — Документация

> **Глобальные сейсмические серии:** статистический анализ 4267 землетрясений M≥6.5 (4418 записей CSV; 2150 BCE – 2026)

**Демо:** [GitHub Pages](https://marshalkin-ux.github.io/paleoseismic-clustering/) · **Статья:** [RU](../paper/article_ru.pdf) · [EN](../paper/article_en.pdf) · **Автор:** [Ярослав Маршалкин](mailto:marshalkin@gmail.com) · Telegram [@MRSHLKN](https://t.me/MRSHLKN)

---

## Описание проекта

**Paleoseismic Clustering** — открытый научный программный комплекс для выявления и статистической проверки **глобальных сейсмических серий** в исторических и инструментальных каталогах землетрясений.

Метод: метрика ближайшего соседа **Baiesi–Paczuski (2004)** с **тектоническим расстоянием** по графу границ плит Bird (2003) вместо евклидова.

### Ключевые результаты (июнь 2026)

| Параметр | Значение |
|----------|----------|
| Каталог | 4267 событий M≥6.5 (4418 CSV-записей) |
| Глобальные серии | 47 (142 кандидата до FDR; исторические p=0.46) |
| Monte Carlo | n = 10 000, p ≤ 0.0001, z = −6.17 |
| ETAS FPR | 1000/1000 (n=1000, N_obs=27; p_ETAS ≤ 0.001) |
| FDR BH (q=0.05) | 45/47 значимы (N=47) |
| Mc / b | 6.55 / 0.911 ± 0.018 |

> **Депонирование:** Zenodo/Figshare/arXiv отложено; код и данные — на [GitHub](https://github.com/marshalkin-ux/paleoseismic-clustering).

---

## Навигация

| № | Файл | Содержание |
|---|------|-----------|
| — | [index.md](index.md) | Главная страница |
| 1 | [01_data_sources.md](01_data_sources.md) | USGS, ISC, NOAA — загрузка и форматы |
| 2 | [02_unified_format.md](02_unified_format.md) | Унификация, дедупликация, SQLite |
| 3 | [03_methodology.md](03_methodology.md) | η-метрика, серии, Monte Carlo, ETAS, FDR |
| 4 | [04_api_reference.md](04_api_reference.md) | API классов и функций |
| 5 | [05_quickstart.md](05_quickstart.md) | Установка и сквозной пример |
| 6 | [06_results_interpretation.md](06_results_interpretation.md) | Интерпретация результатов |
| 7 | [07_contributing.md](07_contributing.md) | Тесты, стиль кода |
| — | [research_improvements_consultation.md](research_improvements_consultation.md) | План улучшений для GRL/BSSA |
| — | [statistical_testing_plan.md](statistical_testing_plan.md) | План статистических тестов |
| — | [implementation_summary.md](implementation_summary.md) | Сводка реализации A–H |

---

## Архитектура

```mermaid
flowchart TD
    subgraph Sources["Источники"]
        A1[USGS ComCat]
        A2[NOAA NGDC]
        A3[ISC Bulletin]
    end

    subgraph Pipeline["Пайплайн"]
        B1[Curator: дедупликация]
        B2[Methodologist: η + тектоника]
        B3[ETAS validation]
        B4[FDR correction]
        B5[Monte Carlo n=10000]
    end

    subgraph Output["Результаты"]
        C1[47 глобальных серий]
        C2[figures/grl/]
        C3[presentation/ HTML + карта]
        C4[paper/article_ru.pdf]
    end

    A1 --> B1
    A2 --> B1
    A3 --> B1
    B1 --> B2 --> B3
    B2 --> B4
    B2 --> B5
    B2 --> C1
    B3 --> C2
    C1 --> C3
    C1 --> C4
```

---

## Статус (июнь 2026)

| Компонент | Статус |
|-----------|--------|
| Загрузка USGS / NOAA / ISC | ✅ |
| Дедупликация, каталог 4418 | ✅ |
| η-кластеризация, глобальные серии | ✅ |
| Monte Carlo n = 10 000 | ✅ |
| ETAS-валидация | ✅ |
| FDR Benjamini–Hochberg | ✅ |
| GRL-фигуры, HTML showcase | ✅ |
| GitHub Pages | ✅ |

**Версия:** 1.0.0 · **Python:** ≥ 3.10 · **Лицензия:** MIT

---

## Публикация и депонирование

**Code and data on GitHub; external deposition (Zenodo) deferred.** См. [PUBLICATION_STATUS.md](../publication/output/PUBLICATION_STATUS.md).

---

## Контакты

- Email: [marshalkin@gmail.com](mailto:marshalkin@gmail.com)
- Telegram: [@MRSHLKN](https://t.me/MRSHLKN)
- Репозиторий: [github.com/marshalkin-ux/paleoseismic-clustering](https://github.com/marshalkin-ux/paleoseismic-clustering)
