# Paleoseismic Clustering — null result: ETAS-validated global series search

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![GitHub Pages](https://img.shields.io/badge/demo-GitHub%20Pages-58a6ff)](https://marshalkin-ux.github.io/paleoseismic-clustering/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/)

**Negative (null/falsification) result:** catalog-calibrated **ETAS** reproduces **N_obs=27** detector episodes (**mean=27.0, p_ETAS=1.0**, FPR 1000/1000) — **no excess global structure** beyond ETAS-like local clustering. Permutation test rejects **temporal Poisson null** (p=0.0001, 1/10,001) — trivial for catalogs with aftershocks; **not** evidence for teleseismic triggering. **47 algorithmic candidates** (not “discovered series”).

> **Живая демонстрация:** [marshalkin-ux.github.io/paleoseismic-clustering](https://marshalkin-ux.github.io/paleoseismic-clustering/)  
> **Научная статья (PDF):** [RU](paper/article_ru.pdf) · [EN](paper/article_en.pdf)  
> **Интерактивная карта:** [presentation/cluster_map_interactive.html](presentation/cluster_map_interactive.html)

**Автор:** [Ярослав Маршалкин](mailto:marshalkin@gmail.com) · Telegram [@MRSHLKN](https://t.me/MRSHLKN)

---

## Ключевые результаты

| Метрика | Значение |
|---------|----------|
| Каталог | **4267** событий M≥6.5 (4418 записей CSV; USGS + ISC + NOAA) |
| Кандидаты детектора | **47** merged (27 modern; **не** физически доказанные «серии») |
| Permutation (Poisson times) | n = 10 000, **p = 0.0001 (1/10 001)**, z = −6.17 — **≠** global-series proof |
| ETAS-null (калибр.) | n = 1000 → **mean 27.0, p_ETAS=1.0**, FPR 1000/1000 |
| Multiseed ETAS | seeds 42–51, n=1000, mean≈27, FPR=1.0 (`results/etas_multiseed.json`) |
| FDR (q = 0.05) | 45/47 on **N=47 post-hoc** — Methods/sensitivity only |
| Эвристика с тект. подсказкой | **98%** GC-фолбэк 1.5× — **failed hypothesis**, not innovation |

---

## О проекте

Проект **проверяет и опровергает** гипотезу о физически значимых **мультирегиональных «глобальных сериях»** в каталоге M≥6.5 (1973–2026 — основное окно).

**Вывод:** применение калиброванной ETAS показывает, что число мультирегиональных кластеров детектора **не превышает** ожидаемого от локальной афтершоковой активности; гипотеза о глобальных сейсмических сериях **не подтверждается**. Permutation отвергает лишь пуассоновский null — тривиально для сейсмических каталогов.

**Методы (без marketing):** η Baiesi–Paczuski; эвристическая метрика с тектонической подсказкой Bird 2003 (98% ≈ scaled Euclidean); permutation test; ETAS validation; FDR sensitivity (Methods).

---

## Публикация и депонирование

**Решение (июнь 2026):** внешнее депонирование (Zenodo и др.) **отложено**. Код и данные — **GitHub** (MIT).

| Артефакт | Ссылка |
|----------|--------|
| HTML-отчёт dry-run | [publication/output/report.html](publication/output/report.html) |
| Статус публикации (RU) | [publication/output/PUBLICATION_STATUS.md](publication/output/PUBLICATION_STATUS.md) |

```bash
pip install -r publication/requirements.txt
python publication/main.py --prepare-only
```

---

## Быстрый старт

```bash
git clone https://github.com/marshalkin-ux/paleoseismic-clustering.git
cd paleoseismic-clustering
pip install -r requirements.txt

python scripts/run_etas_validation.py
python scripts/run_etas_multiseed.py --run --seeds 42,43,44,45,46
python scripts/apply_fdr_correction.py
python scripts/generate_grl_figures.py
python scripts/generate_article_pdf.py
python scripts/generate_article_en_pdf.py
```

**Требования:** Python 3.10+ · [docs/05_quickstart.md](docs/05_quickstart.md)

---

## Структура репозитория

```
paleoseismic-clustering/
├── presentation/project_showcase.html
├── paper/article_ru.md · article_en.md · main.tex
├── results/etas_validation.json · etas_multiseed.json · clustering_sensitivity_strict.json
├── src/analysis/   # clustering, ETAS, FDR
└── scripts/        # CLI pipeline
```

---

## Цитирование

```bibtex
@software{marshalkin2026paleoseismic,
  author  = {Маршалкин, Ярослав},
  title   = {Paleoseismic Clustering: Null Result for Global Seismic Series (ETAS-validated)},
  year    = {2026},
  url     = {https://github.com/marshalkin-ux/paleoseismic-clustering},
  note    = {4267 M≥6.5 events; ETAS p=1.0; falsification of multi-regional global series hypothesis}
}
```

---

## Лицензия

MIT License — см. [LICENSE](LICENSE).

**Контакты:** [marshalkin@gmail.com](mailto:marshalkin@gmail.com) · [@MRSHLKN](https://t.me/MRSHLKN)
