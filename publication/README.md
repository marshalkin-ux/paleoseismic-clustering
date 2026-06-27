# Автоматизация публикации

Подсистема для депонирования статьи **Global Seismic Series** (47 серий, ETAS, FDR) на научных платформах.

**Автор:** Ярослав Маршалкин · [marshalkin@gmail.com](mailto:marshalkin@gmail.com) · [@MRSHLKN](https://t.me/MRSHLKN)

## Установка

```bash
pip install -r publication/requirements.txt
cp publication/config/.env.example publication/config/.env
# Заполните токены в .env (не коммитьте секреты!)
```

## Быстрый старт

```bash
# Только метаданные и zip-архивы
python publication/main.py --prepare-only

# Полный поток в mock-режиме (без реальных API)
python publication/main.py --dry-run

# Отдельные платформы
python publication/main.py --platforms zenodo
python publication/main.py --platforms zenodo,figshare,arxiv --dry-run

# Без соцсетей (ResearchGate / Academia)
python publication/main.py --dry-run --skip-social
```

Альтернативный запуск:

```bash
python -m publication.main --dry-run
```

## Архитектура

| Агент | Файл | Назначение |
|-------|------|------------|
| 1 | `agents/orchestrator.py` | Координация потока |
| 2 | `agents/zenodo.py` | DOI через Zenodo |
| 3 | `agents/figshare.py` | Figshare |
| 4 | `agents/arxiv.py` | arXiv |
| 5 | `agents/osf_eartharxiv.py` | OSF / EarthArXiv |
| 6 | `agents/data_repos.py` | PANGAEA, GFZ, Dryad |
| 7 | `agents/social_upload.py` | ResearchGate, Academia (Selenium) |
| 8 | `agents/monitor.py` | HTML-отчёт |

Порядок: **init → Zenodo (DOI) → параллельно Figshare/OSF/PANGAEA/GFZ/Dryad → arXiv → social → GitHub stub → report**.

## Выходные файлы

- `output/master_metadata.json` — мастер-метаданные (RU/EN)
- `output/supplementary.zip`, `code.zip`, `figures.zip`
- `output/report.html` — статус публикации
- `logs/` — журналы loguru

## Ручные шаги

1. **arXiv** — новым авторам нужен endorser; первую заявку подают вручную.
2. **ResearchGate / Academia.edu** — Selenium + ручной CAPTCHA/логин (`SOCIAL_UPLOAD_LIVE=true`, `SELENIUM_HEADLESS=false`).
3. **PANGAEA / GFZ / Dryad** — модерация; агент опрашивает статус, финальное одобрение может занять дни.

## Тесты

```bash
python -m pytest publication/tests/ -v
```

## Безопасность

- Без токенов в `.env` система работает в **mock/dry-run** — реальные API не вызываются.
- Файл `.env` в `.gitignore`; используйте `.env.example` как шаблон.

English documentation: [README_en.md](README_en.md)
