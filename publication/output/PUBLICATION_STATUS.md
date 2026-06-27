# Статус публикации — Paleoseismic Clustering

**Дата:** 2026-06-27  
**Решение автора:** внешнее депонирование **отложено** (Zenodo, Figshare, arXiv, OSF, EarthArXiv и др.).  
**Текущий канал распространения:** GitHub only — [github.com/marshalkin-ux/paleoseismic-clustering](https://github.com/marshalkin-ux/paleoseismic-clustering)

Папка `publication/` сохранена как **инструмент будущей автоматизации** (метаданные, zip-архивы, dry-run). Живые API **не вызываются** и **не планируются** в ближайшем цикле работ.

---

## Что доступно сейчас

| Ресурс | Статус |
|--------|--------|
| GitHub (код + данные + статья PDF/MD) | ✅ основной |
| GitHub Pages (демо) | ✅ |
| Zenodo / Figshare / arXiv DOI | ⏸ отложено |
| `publication/` dry-run | ✅ mock only |

## Последний автоматический прогон (mock)

| Шаг | Команда | Результат |
|-----|---------|-----------|
| Подготовка метаданных | `python publication/main.py --prepare-only` | OK (локально) |
| Dry-run | `python publication/main.py --dry-run --skip-social` | OK (mock DOI) |
| Тесты | `python -m pytest publication/tests/ -v` | 10/10 passed |

Mock DOI в `master_metadata.json` и `report.html` **не являются реальными** и не должны цитироваться.

## Когда понадобится внешний депозит

1. Создать `publication/config/.env` из `.env.example` (токены Zenodo и др.).
2. Прогнать sandbox: `ZENODO_USE_SANDBOX=true python publication/main.py --skip-social`
3. Обновить `CITATION.cff` реальным DOI.

До этого момента цитируйте репозиторий GitHub (см. [CITATION.cff](../CITATION.cff)).

## Контакты

Ярослав Маршалкин · marshalkin@gmail.com · [@MRSHLKN](https://t.me/MRSHLKN)
