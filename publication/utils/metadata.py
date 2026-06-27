"""Extract publication metadata from project sources."""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml
from loguru import logger


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def publication_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_title(content: str) -> str:
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _extract_section(content: str, heading: str) -> str:
    pattern = rf"^##\s+{re.escape(heading)}\s*\n\n(.+?)(?=\n##\s|\n---|\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if not match:
        return ""
    text = match.group(1).strip()
    text = re.sub(r"\*\*Keywords:\*\*.*", "", text, flags=re.DOTALL).strip()
    return text.split("\n\n**Keywords")[0].strip()


def _extract_keywords(content: str, label: str) -> list[str]:
    pattern = rf"\*\*{re.escape(label)}:\*\*\s*(.+)$"
    match = re.search(pattern, content, re.MULTILINE)
    if not match:
        return []
    raw = match.group(1).strip()
    parts = re.split(r"[;·,]", raw)
    return [p.strip() for p in parts if p.strip()]


def _parse_citation_cff(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(_read_text(path)) or {}
    authors = []
    for author in data.get("authors", []):
        given = author.get("given-names", "")
        family = author.get("family-names", "")
        name_en = f"{given} {family}".strip()
        authors.append(
            {
                "name_en": name_en,
                "name_ru": name_en,
                "email": author.get("email", ""),
                "orcid": author.get("orcid", ""),
            }
        )
    return {
        "authors": authors,
        "repository_code": data.get("repository-code", ""),
        "url": data.get("url", ""),
        "keywords_en": data.get("keywords", []),
        "version": data.get("version", "1.0.0"),
        "date_released": data.get("date-released", str(date.today())),
        "license": data.get("license", "MIT"),
    }


def build_metadata(
    root: Path | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    """Build master_metadata.json from article files and CITATION.cff."""
    root = root or repo_root()
    paper = root / "paper"
    en_md = _read_text(paper / "article_en.md")
    ru_md = _read_text(paper / "article_ru.md")
    cff = _parse_citation_cff(root / "CITATION.cff")

    metadata: dict[str, Any] = {
        "title_en": _extract_title(en_md),
        "title_ru": _extract_title(ru_md),
        "abstract_en": _extract_section(en_md, "Abstract"),
        "abstract_ru": _extract_section(ru_md, "Аннотация"),
        "keywords_en": _extract_keywords(en_md, "Keywords") or cff.get("keywords_en", []),
        "keywords_ru": _extract_keywords(ru_md, "Ключевые слова"),
        "authors": cff.get("authors") or [
            {
                "name_en": "Yaroslav Marshalkin",
                "name_ru": "Ярослав Маршалкин",
                "email": "marshalkin@gmail.com",
                "orcid": "",
            }
        ],
        "affiliations": [],
        "doi": "",
        "zenodo_url": "",
        "figshare_doi": "",
        "arxiv_id": "",
        "osf_url": "",
        "eartharxiv_url": "",
        "pangaea_doi": "",
        "gfz_doi": "",
        "dryad_doi": "",
        "researchgate_status": "pending",
        "academia_status": "pending",
        "github_url": cff.get("repository_code", "https://github.com/marshalkin-ux/paleoseismic-clustering"),
        "publication_date": str(cff.get("date_released") or date.today()),
        "version": cff.get("version", "1.0.0"),
        "license": cff.get("license", "MIT"),
        "project_url": cff.get("url", ""),
        "files": {},
        "platform_status": {},
    }

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Wrote metadata to {}", output_path)

    return metadata


def load_metadata(path: Path) -> dict[str, Any]:
    if not path.exists():
        return build_metadata(output_path=path)
    return json.loads(path.read_text(encoding="utf-8"))


def save_metadata(path: Path, metadata: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
