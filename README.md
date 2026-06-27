# Paleoseismic Clustering — глобальные сейсмические серии

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![GitHub Pages](https://img.shields.io/badge/demo-GitHub%20Pages-58a6ff)](https://marshalkin-ux.github.io/paleoseismic-clustering/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)

**Статистически значимые глобальные сейсмические серии** в четырёхтысячелетнем каталоге **4267 событий M≥6.5** (4418 записей CSV); **основной анализ значимости — современное окно 1973–2026** (2041 событие, 27 серий при p=0.0001, 1/10 001 перестановка). Тектоническое расстояние (98% GC-фолбэк), метрика [Baiesi–Paczuski](https://en.wikipedia.org/wiki/Earthquake_clustering), [ETAS](https://en.wikipedia.org/wiki/Epidemic-type_aftershock_sequence)-валидация (n=1000, FPR 1000/1000), [FDR](https://en.wikipedia.org/wiki/False_discovery_rate) (N=47, 45/47) и Monte Carlo.

> **Живая демонстрация:** [marshalkin-ux.github.io/paleoseismic-clustering](https://marshalkin-ux.github.io/paleoseismic-clustering/)  
> **Научная статья (PDF):** [RU](paper/article_ru.pdf) · [EN](paper/article_en.pdf)  
> **Интерактивная карта:** [presentation/cluster_map_interactive.html](presentation/cluster_map_interactive.html)

**Автор:** [Ярослав Маршалкин](mailto:marshalkin@gmail.com) · Telegram [@MRSHLKN](https://t.me/MRSHLKN)

---

## Ключевые результаты

| Метрика | Значение |
|---------|----------|
| Каталог | **4267** событий M≥6.5 (4418 записей CSV; USGS + ISC + NOAA) |
| Глобальные серии | **47** (27 modern p=0.0001 · 15 ранних · 5 исторических; FDR 45/47) |
| Monte Carlo | n = 10 000, **p = 0.0001 (1/10 001)**, z = −6.17 |
| ETAS-валидация | n = 1000 → **FPR 1000/1000** (калибр. null: mean 27,0, p_ETAS=1,0; N_obs=27) |
| FDR (q = 0.05) | **45/47** серий значимы (**N = 47** гипотез) |
| Mc / b-value | 6.55 / 0.911 ± 0.018 |

---

## О проекте

Проект ищет **глобальные сейсмические серии** — эпизоды, когда крупные землетрясения (M≥6.5) в географически удалённых регионах происходят **теснее**, чем при случайном (пуассоновском) распределении.

**Методологические отличия от классических работ:**

- **Тектоническое расстояние** (Bird 2003): протестировано как замена евклидова; **98%** пар — GC-фолбэк 1,5×, эффект только у **~2%** граничных пар (отрицательный результат для глобального анализа)
- Метрика ближайшего соседа **η** (Baiesi & Paczuski 2004)
- Трёхуровневая статистическая валидация: permutation test · ETAS null model · FDR Benjamini–Hochberg
- Заявления о значимости — для **1973–2026** (2041 событие) и раннего инструментального периода **1900–1972**; данные до 1900 г. не значимы (p=0.46)

**Ключевые слова (SEO):** global seismic series · earthquake clustering · remote triggering · tectonic distance · ETAS validation · paleoseismic catalog · Baiesi-Paczuski metric · Monte Carlo permutation test · FDR multiple testing · глобальные сейсмические серии · кластеризация землетрясений · дальнодействующий триггеринг

---

## Публикация и депонирование

**Решение (июнь 2026):** внешнее депонирование (Zenodo, Figshare, arXiv, OSF и др.) **отложено**. Код и данные — **только на GitHub** (MIT). Папка `publication/` — инструмент будущей автоматизации, без срочности и без живых API.

| Артефакт | Ссылка |
|----------|--------|
| HTML-отчёт dry-run | [publication/output/report.html](publication/output/report.html) |
| Статус публикации (RU) | [publication/output/PUBLICATION_STATUS.md](publication/output/PUBLICATION_STATUS.md) |
| Метаданные | [publication/output/master_metadata.json](publication/output/master_metadata.json) |

```bash
pip install -r publication/requirements.txt
python publication/main.py --prepare-only
python publication/main.py --dry-run --skip-social
```

> **DOI:** placeholder `10.5281/zenodo.XXXXXXX` в [CITATION.cff](CITATION.cff) — обновится при внешнем депозите (сейчас отложено; см. [PUBLICATION_STATUS.md](publication/output/PUBLICATION_STATUS.md)).

---

## Быстрый старт

```bash
git clone https://github.com/marshalkin-ux/paleoseismic-clustering.git
cd paleoseismic-clustering
pip install -r requirements.txt

# Экспорт данных для интерактивной карты
python scripts/export_map_data.py

# ETAS-валидация и FDR
python scripts/run_etas_validation.py
python scripts/apply_fdr_correction.py

# Фигуры для статьи
python scripts/generate_grl_figures.py
python scripts/generate_visualizations.py
python scripts/generate_article_pdf.py
```

**Требования:** Python 3.10+

Подробнее: [docs/05_quickstart.md](docs/05_quickstart.md)

---

## Структура репозитория

```
paleoseismic-clustering/
├── index.html                    # GitHub Pages → showcase
├── presentation/
│   ├── project_showcase.html     # Главная HTML-презентация
│   ├── cluster_map_interactive.html
│   └── map_events_embed.js       # Данные карты (4267+ событий)
├── paper/
│   ├── article_ru.pdf            # Научная статья (RU)
│   ├── article_ru.md
│   ├── article_en.pdf            # Scientific article (EN)
│   ├── article_en.md
│   └── main.tex                  # Шаблон GRL/BSSA
├── figures/grl/                  # Публикационные рисунки
├── results/                      # JSON-результаты анализа
├── src/                          # Python-пакет
├── scripts/                      # Пайплайн и генераторы
└── docs/                         # Документация (7 разделов)
```

---

## Архитектура

```
USGS + ISC + NOAA  →  Curator (дедупликация)  →  Methodologist (η + тектоника)
                                                      ↓
                              ETAS validation · FDR · Monte Carlo  →  Results + Figures
```

| Модуль | Назначение |
|--------|------------|
| `src/curator/` | Загрузка USGS, NOAA, ISC; дедупликация; SQLite |
| `src/analysis/` | Mc, b-value, тектоническое расстояние, η-кластеризация, Monte Carlo |
| `src/analysis/etas_validation.py` | ETAS-генератор, false-positive analysis |
| `src/analysis/multiple_testing.py` | Bonferroni, Holm, FDR |
| `scripts/` | CLI: загрузка, анализ, валидация, фигуры |

---

## Документация

| Раздел | Файл |
|--------|------|
| Обзор | [docs/index.md](docs/index.md) |
| Источники данных | [docs/01_data_sources.md](docs/01_data_sources.md) |
| Методология | [docs/03_methodology.md](docs/03_methodology.md) |
| API | [docs/04_api_reference.md](docs/04_api_reference.md) |
| Быстрый старт | [docs/05_quickstart.md](docs/05_quickstart.md) |
| Интерпретация | [docs/06_results_interpretation.md](docs/06_results_interpretation.md) |
| Доступность данных | [docs/data_availability.md](docs/data_availability.md) |
| GRL/BSSA план | [docs/research_improvements_consultation.md](docs/research_improvements_consultation.md) |

---

## Тесты

```bash
pytest tests/ -v
```

---

## Цитирование

```bibtex
@software{marshalkin2026paleoseismic,
  author  = {Маршалкин, Ярослав},
  title   = {Paleoseismic Clustering: Global Seismic Series Detection},
  year    = {2026},
  url     = {https://github.com/marshalkin-ux/paleoseismic-clustering},
  note    = {4267 M≥6.5 events, 47 global series (45/47 FDR), ETAS-validated}
}
```

Ключевые методологические работы: Baiesi & Paczuski (2004), Bird (2003), Zaliapin & Ben-Zion (2013).

---

## Лицензия

MIT License — см. [LICENSE](LICENSE).

## Контакты

- **Email:** [marshalkin@gmail.com](mailto:marshalkin@gmail.com)
- **Telegram:** [@MRSHLKN](https://t.me/MRSHLKN)
- **GitHub:** [marshalkin-ux/paleoseismic-clustering](https://github.com/marshalkin-ux/paleoseismic-clustering)
