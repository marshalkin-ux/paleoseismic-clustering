# Publication Automation

Automated deposition workflow for **Global Seismic Series** (47 series, ETAS, FDR) across scientific platforms.

**Author:** Yaroslav Marshalkin · [marshalkin@gmail.com](mailto:marshalkin@gmail.com) · [@MRSHLKN](https://t.me/MRSHLKN)

## Setup

```bash
pip install -r publication/requirements.txt
cp publication/config/.env.example publication/config/.env
# Fill in tokens — never commit real secrets
```

## Usage

```bash
python publication/main.py --prepare-only   # metadata + zip packages
python publication/main.py --dry-run          # full mock workflow
python publication/main.py --platforms zenodo
python publication/main.py --platforms zenodo,figshare --skip-social
```

## Orchestrator sequence

1. **init** — extract metadata from `paper/article_*.md` + `CITATION.cff`, build zips
2. **Zenodo** — register DOI
3. **Parallel** — Figshare, OSF, PANGAEA, GFZ, Dryad
4. **arXiv** — preprint submission (stub / manual endorser)
5. **Social** — ResearchGate, Academia (Selenium, manual CAPTCHA)
6. **GitHub** — README DOI stub
7. **Report** — `output/report.html`

## Manual intervention required

| Platform | Action |
|----------|--------|
| arXiv | Obtain endorser for first submission |
| ResearchGate / Academia | Browser login + CAPTCHA via Selenium |
| PANGAEA / GFZ / Dryad | Editorial moderation (polling only) |

## Tests

```bash
python -m pytest publication/tests/ -v
```

Russian documentation: [README.md](README.md)
