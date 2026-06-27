"""Pytest fixtures for publication subsystem."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "publication"


@pytest.fixture
def repo_root() -> Path:
    return ROOT


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    return tmp_path / "output"


@pytest.fixture
def sample_metadata() -> dict:
    return {
        "title_en": "Test Title EN",
        "title_ru": "Тестовый заголовок",
        "abstract_en": "Abstract EN text.",
        "abstract_ru": "Аннотация RU.",
        "keywords_en": ["earthquake", "clustering"],
        "keywords_ru": ["землетрясение", "кластеризация"],
        "authors": [{"name_en": "Yaroslav Marshalkin", "name_ru": "Ярослав Маршалкин", "email": "marshalkin@gmail.com"}],
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
        "github_url": "https://github.com/marshalkin-ux/paleoseismic-clustering",
        "publication_date": "2026-06-27",
        "files": {},
        "platform_status": {},
    }


@pytest.fixture
def metadata_path(output_dir: Path, sample_metadata: dict) -> Path:
    path = output_dir / "master_metadata.json"
    path.write_text(json.dumps(sample_metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
