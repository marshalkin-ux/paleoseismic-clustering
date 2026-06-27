# Статус публикации — Paleoseismic Clustering

**Дата прогона:** 2026-06-27  
**Режим:** prepare-only + dry-run (mock) — **живая публикация не выполнялась**

## Что выполнено автоматически

| Шаг | Команда | Результат |
|-----|---------|-----------|
| Установка зависимостей | `pip install -r publication/requirements.txt` | OK |
| Подготовка метаданных и архивов | `python publication/main.py --prepare-only` | OK |
| Dry-run всех платформ | `python publication/main.py --dry-run --skip-social` | OK |
| Тесты | `python -m pytest publication/tests/ -v` | **10/10 passed** |

## Сгенерированные артефакты

| Файл | Описание |
|------|----------|
| [master_metadata.json](master_metadata.json) | Метаданные + mock DOI со всех платформ |
| [report.html](report.html) | HTML-отчёт о статусе публикации |
| [supplementary.zip](supplementary.zip) | Статья (PDF/MD), описания данных |
| [code.zip](code.zip) | Исходный код и скрипты |
| [figures.zip](figures.zip) | Фигуры из `paper/figures/` |
| [data_description_ru.md](data_description_ru.md) | Описание набора данных (RU) |
| [data_description_en.md](data_description_en.md) | Описание набора данных (EN) |

## Mock DOI (dry-run — не реальные идентификаторы)

| Платформа | Mock идентификатор | Статус |
|-----------|-------------------|--------|
| Zenodo | `10.5281/zenodo.1234567` | mock |
| Figshare | `10.6084/m9.figshare.9876543` | mock |
| OSF | `https://osf.io/abc12/` | mock |
| EarthArXiv | `https://eartharxiv.org/repository/view/1234/` | mock |
| PANGAEA | `10.1594/PANGAEA.123456` | mock |
| GFZ | `10.5880/GFZ.2026.001` | mock |
| Dryad | `10.5061/dryad.abc123` | mock |
| arXiv | `2026.12345` | mock |
| ResearchGate / Academia | — | пропущено (`--skip-social`) |
| GitHub README DOI | — | пропущено (dry-run) |

## Почему живая публикация невозможна

Файл `publication/config/.env` **отсутствует**. Переменная окружения `ZENODO_ACCESS_TOKEN` **не задана**.

Без токенов API Zenodo, Figshare, OSF, arXiv и репозиториев данных **не вызываются** — система автоматически переходит в mock/dry-run режим.

> **Не создавайте `.env` с фиктивными токенами** — запросы будут падать с ошибками авторизации.

## Шаги для живой публикации

### 1. Zenodo (основной DOI)

1. Зарегистрируйтесь на [zenodo.org](https://zenodo.org/) (или [sandbox.zenodo.org](https://sandbox.zenodo.org/) для теста).
2. **Settings → Applications → Personal access tokens → New token** (scope: `deposit:actions`, `deposit:write`).
3. Скопируйте шаблон: `cp publication/config/.env.example publication/config/.env`
4. Вставьте токен:
   ```
   ZENODO_ACCESS_TOKEN=your_token_here
   ZENODO_USE_SANDBOX=true   # false для production zenodo.org
   ```
5. Запустите без `--dry-run`:
   ```bash
   pip install -r publication/requirements.txt
   python publication/main.py --skip-social
   ```
6. После успешного депозита обновите `CITATION.cff` реальным DOI и `README.md`.

### 2. Figshare

1. [figshare.com](https://figshare.com/) → Account Settings → API tokens.
2. Добавьте в `.env`: `FIGSHARE_TOKEN=...`

### 3. OSF / EarthArXiv

1. [osf.io](https://osf.io/) → Settings → Personal Access Tokens.
2. Добавьте в `.env`: `OSF_TOKEN=...`, `OSF_PROJECT_ID=...`

### 4. arXiv

1. Зарегистрируйтесь на [arxiv.org](https://arxiv.org/user/register).
2. Получите endorser (первичная подача).
3. Добавьте в `.env`: `ARXIV_USERNAME=...`, `ARXIV_PASSWORD=...`

### 5. PANGAEA / GFZ / Dryad

Требуют ручной модерации и отдельные токены — см. `publication/config/.env.example`.

### 6. ResearchGate / Academia.edu

Selenium-автоматизация с ручным CAPTCHA. Установите `SOCIAL_UPLOAD_LIVE=true` и учётные данные в `.env`. Запуск без `--skip-social`.

### 7. Обновление CITATION.cff и README

После получения реального DOI от Zenodo:

```yaml
# CITATION.cff
doi: 10.5281/zenodo.REAL_ID
```

Перезапустите `python publication/main.py --prepare-only` для обновления метаданных.

## Проверка перед production

```bash
# Sandbox Zenodo (рекомендуется сначала)
ZENODO_USE_SANDBOX=true python publication/main.py --skip-social

# Production (после проверки sandbox)
# ZENODO_USE_SANDBOX=false python publication/main.py --skip-social
```

## Контакты

Ярослав Маршалкин · marshalkin@gmail.com · [@MRSHLKN](https://t.me/MRSHLKN)
