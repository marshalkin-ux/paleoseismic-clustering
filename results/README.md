# Результаты анализа — Paleoseismic Clustering

**Дата прогона:** 2026-06-27  
**Автор:** [Ярослав Маршалкин](mailto:marshalkin@gmail.com) · Telegram [@MRSHLKN](https://t.me/MRSHLKN)

---

## Каталог

| Параметр | Значение |
|----------|----------|
| Источники | USGS ComCat + ISC Bulletin + NOAA NGDC |
| Событий M ≥ 6.5 | **4267** (4418 записей CSV) |
| Диапазон | 2150 BCE – 2026 |
| Эпохи | 47 исторических · 2179 ранних · 2041 современных |
| Mc / b-value | 6.55 / 0.911 ± 0.018 |

---

## Глобальные серии

| Параметр | Значение |
|----------|----------|
| Всего значимых серий | **47** |
| Современный период (1973–2026) | 27 серий, p < 0.0001 |
| Ранний инструментальный (1900–1972) | 15 серий, p = 0.007 |
| Исторический (до 1900) | 5 серий |
| Кандидатов до FDR | 142 |

### Топ-серии

| ID | N | Регионов | Период | Mmax |
|----|---|----------|--------|------|
| S047 | 53 | 5 | 1982–2024 | 8.0 |
| S170 | 46 | 12 | 2002–2023 | **9.1** |
| S015 | 27 | 2 | 1975–2006 | 8.0 |

---

## Статистическая валидация

| Тест | Результат |
|------|-----------|
| Monte Carlo (n = 10 000) | p < 0.0001, z = −6.17 |
| ETAS (100 каталогов) | 0 ложных серий, p_ETAS = 0.0000 |
| FDR BH (q = 0.05) | 45/47 значимы |
| Декластеризация GK / ZBZ | 98.8% / 100.0% независимых |

---

## Файлы результатов

### JSON (доступны в репозитории)

| Файл | Описание |
|------|----------|
| `analysis_full_historical.json` | Серии по трём эпохам |
| `analysis_summary.json` | Краткое резюме + Monte Carlo |
| `etas_validation.json` | ETAS null-model validation |
| `montecarlo_full.json` | Полный Monte Carlo прогон |
| `clusters.json` | Кластеры и серии |

### CSV (локально, не в git)

Большие CSV (`cluster_summary.csv`, `events_with_nn.csv`) генерируются пайплайном локально и исключены из git из-за размера. Воспроизведите: `python scripts/run_analysis.py`.

---

## Визуализации

- `figures/grl/` — 5 рисунков для GRL/BSSA
- `figures/viz1_*.png` … `viz6_*.png` — демо-графики
- `presentation/project_showcase.html` — интерактивная презентация
- `presentation/cluster_map_interactive.html` — карта всех событий

---

## Воспроизведение

```bash
python scripts/run_etas_validation.py
python scripts/apply_fdr_correction.py
python scripts/generate_grl_figures.py
```

Подробнее: [docs/05_quickstart.md](../docs/05_quickstart.md) · [analysis_status.md](analysis_status.md)
