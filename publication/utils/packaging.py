"""Package supplementary materials, code, and figures for upload."""

from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape
from loguru import logger

from publication.utils.metadata import repo_root, save_metadata


def _zip_directory(source: Path, archive: Path, arc_prefix: str = "") -> None:
    archive.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        if source.is_file():
            zf.write(source, arc_prefix or source.name)
            return
        for path in sorted(source.rglob("*")):
            if path.is_file():
                rel = path.relative_to(source)
                zf.write(path, str(Path(arc_prefix) / rel) if arc_prefix else str(rel))


def _copy_if_exists(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    return True


def render_data_descriptions(output_dir: Path, metadata: dict[str, Any]) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    templates_dir = Path(__file__).resolve().parents[1] / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(enabled_extensions=()),
    )
    rendered: dict[str, Path] = {}
    for lang, template_name in (("en", "data_description_en.md.j2"), ("ru", "data_description_ru.md.j2")):
        template = env.get_template(template_name)
        text = template.render(metadata=metadata)
        out = output_dir / f"data_description_{lang}.md"
        out.write_text(text, encoding="utf-8")
        rendered[lang] = out
    return rendered


def create_packages(
    metadata: dict[str, Any],
    output_dir: Path | None = None,
    root: Path | None = None,
) -> dict[str, Any]:
    """Create zip archives and per-platform folders."""
    root = root or repo_root()
    output_dir = output_dir or Path(__file__).resolve().parents[1] / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    descriptions = render_data_descriptions(output_dir, metadata)
    manifest: dict[str, Any] = {}

    supplementary_files = [
        root / "paper" / "article_en.pdf",
        root / "paper" / "article_ru.pdf",
        root / "paper" / "article_en.md",
        root / "paper" / "article_ru.md",
        descriptions["en"],
        descriptions["ru"],
        root / "data" / "processed" / "unified_catalog_full.csv",
        root / "results" / "clusters.json",
        root / "results" / "etas_validation.json",
        root / "results" / "fdr_correction_results.csv",
    ]
    supp_dir = output_dir / "_supplementary_staging"
    if supp_dir.exists():
        shutil.rmtree(supp_dir)
    supp_dir.mkdir(parents=True)
    for src in supplementary_files:
        if src.exists():
            dst = supp_dir / src.name
            shutil.copy2(src, dst)
    supp_zip = output_dir / "supplementary.zip"
    _zip_directory(supp_dir, supp_zip)
    manifest["supplementary.zip"] = str(supp_zip)
    shutil.rmtree(supp_dir)

    code_items = [
        root / "src",
        root / "scripts",
        root / "requirements.txt",
        root / "pyproject.toml",
        root / "CITATION.cff",
        root / "LICENSE",
    ]
    code_dir = output_dir / "_code_staging"
    if code_dir.exists():
        shutil.rmtree(code_dir)
    code_dir.mkdir()
    for item in code_items:
        if item.exists():
            dst = code_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dst)
            else:
                shutil.copy2(item, dst)
    code_zip = output_dir / "code.zip"
    _zip_directory(code_dir, code_zip)
    manifest["code.zip"] = str(code_zip)
    shutil.rmtree(code_dir)

    figures_dir = root / "figures"
    fig_zip = output_dir / "figures.zip"
    if figures_dir.exists():
        _zip_directory(figures_dir, fig_zip)
        manifest["figures.zip"] = str(fig_zip)

    platform_dirs = ["zenodo", "figshare", "arxiv", "osf", "pangaea", "gfz", "dryad"]
    for platform in platform_dirs:
        plat_dir = output_dir / platform
        plat_dir.mkdir(parents=True, exist_ok=True)
        for archive_name in ("supplementary.zip", "code.zip", "figures.zip"):
            archive = output_dir / archive_name
            if archive.exists():
                shutil.copy2(archive, plat_dir / archive.name)
        readme = plat_dir / "README.txt"
        readme.write_text(
            f"Upload bundle for {platform}\nTitle: {metadata.get('title_en', '')}\n",
            encoding="utf-8",
        )

    metadata["files"] = manifest
    meta_path = output_dir / "master_metadata.json"
    save_metadata(meta_path, metadata)
    logger.info("Created packages in {}", output_dir)
    return manifest
