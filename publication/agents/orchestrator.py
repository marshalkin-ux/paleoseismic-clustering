"""Agent 1 — Publication workflow orchestrator."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from loguru import logger

from publication.agents.arxiv import ArxivAgent
from publication.agents.data_repos import DataReposAgent
from publication.agents.figshare import FigshareAgent
from publication.agents.monitor import MonitorAgent
from publication.agents.osf_eartharxiv import OSFEarthArxivAgent
from publication.agents.social_announce import SocialAnnounceAgent
from publication.agents.social_upload import SocialUploadAgent
from publication.agents.zenodo import ZenodoAgent
from publication.utils.metadata import build_metadata, load_metadata, repo_root, save_metadata
from publication.utils.packaging import create_packages


class Orchestrator:
    """Coordinate publication agents in dependency order."""

    PARALLEL_AFTER_ZENODO = ("figshare", "osf", "pangaea", "gfz", "dryad")

    def __init__(
        self,
        *,
        dry_run: bool = False,
        prepare_only: bool = False,
        skip_social: bool = False,
        platforms: list[str] | None = None,
        output_dir: Path | None = None,
        config_path: Path | None = None,
    ) -> None:
        self.root = repo_root()
        self.publication_dir = Path(__file__).resolve().parents[1]
        self.output_dir = output_dir or self.publication_dir / "output"
        self.config_path = config_path or self.publication_dir / "config" / "platforms.yaml"
        self.dry_run = dry_run
        self.prepare_only = prepare_only
        self.skip_social = skip_social
        self.platforms = platforms or self._default_platforms()
        self.mock_mode = dry_run or self._detect_mock_mode()
        self._load_env()

    def _load_env(self) -> None:
        env_path = self.publication_dir / "config" / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()

    def _default_platforms(self) -> list[str]:
        if not self.config_path.exists():
            return ["zenodo", "figshare", "osf", "pangaea", "gfz", "dryad", "arxiv"]
        data = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
        return [p["id"] for p in data.get("platforms", []) if p.get("enabled", True)]

    def _detect_mock_mode(self) -> bool:
        required = {
            "zenodo": "ZENODO_ACCESS_TOKEN",
            "figshare": "FIGSHARE_TOKEN",
            "osf": "OSF_TOKEN",
            "arxiv": "ARXIV_USERNAME",
        }
        for platform in self.platforms:
            token = required.get(platform)
            if token and not os.getenv(token):
                logger.info("Missing {} — enabling mock mode for {}", token, platform)
                return True
        return False

    def init(self) -> dict[str, Any]:
        logger.info("Phase: init — metadata and packaging")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        meta_path = self.output_dir / "master_metadata.json"
        metadata = build_metadata(self.root, meta_path)
        create_packages(metadata, self.output_dir, self.root)
        return load_metadata(meta_path)

    def _update_github_readme_stub(self, metadata: dict[str, Any]) -> None:
        readme = self.root / "README.md"
        if not readme.exists():
            return
        marker = "<!-- publication-doi -->"
        doi_line = f"**DOI:** [{metadata.get('doi') or 'pending'}]({metadata.get('zenodo_url') or '#'})"
        content = readme.read_text(encoding="utf-8")
        if marker in content:
            return
        stub = f"\n{marker}\n{doi_line}\n"
        readme.write_text(content.rstrip() + stub, encoding="utf-8")
        metadata.setdefault("platform_status", {})["github"] = {
            "status": "stub_updated",
            "note": "README DOI marker appended — review before commit.",
        }
        logger.info("GitHub README stub updated with DOI marker")

    def run(self) -> dict[str, Any]:
        metadata = self.init()
        if self.prepare_only:
            logger.info("Prepare-only mode — stopping after packaging")
            MonitorAgent(self.output_dir).generate_report(metadata)
            return metadata

        mock = self.dry_run or self.mock_mode
        logger.info("Running publication flow (mock={}, platforms={})", mock, self.platforms)

        if "zenodo" in self.platforms:
            ZenodoAgent(mock_mode=mock, output_dir=self.output_dir).upload(metadata)
            save_metadata(self.output_dir / "master_metadata.json", metadata)

        parallel_platforms = [p for p in self.PARALLEL_AFTER_ZENODO if p in self.platforms]
        if parallel_platforms:
            self._run_parallel(parallel_platforms, metadata, mock)

        if "arxiv" in self.platforms:
            ArxivAgent(mock_mode=mock, output_dir=self.output_dir).upload(metadata)

        if not self.skip_social and "social" in self.platforms:
            SocialUploadAgent(mock_mode=mock, output_dir=self.output_dir).upload(metadata)

        if not self.skip_social:
            SocialAnnounceAgent().announce(metadata, dry_run=mock)

        if not mock:
            self._update_github_readme_stub(metadata)
        else:
            metadata.setdefault("platform_status", {})["github"] = {
                "status": "skipped_mock",
                "note": "README DOI stub skipped in dry-run/mock mode.",
            }
        save_metadata(self.output_dir / "master_metadata.json", metadata)
        MonitorAgent(self.output_dir).generate_report(metadata)
        return metadata

    def _run_parallel(self, platforms: list[str], metadata: dict[str, Any], mock: bool) -> None:
        agents: dict[str, Any] = {
            "figshare": lambda: FigshareAgent(mock_mode=mock, output_dir=self.output_dir).upload(metadata),
            "osf": lambda: OSFEarthArxivAgent(mock_mode=mock, output_dir=self.output_dir).upload(metadata),
        }
        data_agent = DataReposAgent(mock_mode=mock, output_dir=self.output_dir)
        for name in ("pangaea", "gfz", "dryad"):
            if name in platforms:
                agents[name] = lambda n=name: data_agent.upload_platform(n, metadata)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(agents[p]): p for p in platforms if p in agents}
            for future in as_completed(futures):
                platform = futures[future]
                try:
                    future.result()
                    logger.info("Parallel platform {} completed", platform)
                except Exception as exc:
                    logger.error("Platform {} failed: {}", platform, exc)
                    metadata.setdefault("platform_status", {})[platform] = {
                        "status": "error",
                        "error": str(exc),
                    }

        save_metadata(self.output_dir / "master_metadata.json", metadata)
