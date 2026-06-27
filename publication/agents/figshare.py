"""Agent 3 — Figshare upload."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from loguru import logger

from publication.utils.api_client import APIClient


class FigshareAgent:
    platform = "figshare"

    def __init__(self, mock_mode: bool = False, output_dir: Path | None = None) -> None:
        self.mock_mode = mock_mode or not os.getenv("FIGSHARE_TOKEN")
        self.output_dir = output_dir or Path(__file__).resolve().parents[1] / "output"
        self.client = APIClient(
            base_url="https://api.figshare.com/v2",
            token=os.getenv("FIGSHARE_TOKEN"),
            mock_mode=self.mock_mode,
        )

    def upload(self, metadata: dict[str, Any]) -> dict[str, Any]:
        logger.info("Figshare agent starting (mock={})", self.mock_mode)
        if self.mock_mode:
            result = {
                "figshare_doi": "10.6084/m9.figshare.9876543",
                "url": "https://figshare.com/articles/dataset/mock/9876543",
                "status": "published",
                "mock": True,
            }
        else:
            article = self.client.request(
                "POST",
                "/account/articles",
                json={
                    "title": metadata["title_en"],
                    "description": metadata["abstract_en"],
                    "defined_type": "dataset",
                    "tags": metadata.get("keywords_en", []),
                },
            )
            article_id = article["id"]
            supp = self.output_dir / "supplementary.zip"
            if supp.exists():
                upload_url = self.client.request(
                    "POST",
                    f"/account/articles/{article_id}/files/upload",
                    json={"fileName": supp.name, "fileSize": supp.stat().st_size},
                )
                self.client.request("PUT", upload_url["uploadUrl"], data=supp.read_bytes())
            published = self.client.request("POST", f"/account/articles/{article_id}/actions/publish")
            result = {
                "figshare_doi": published.get("doi", ""),
                "url": published.get("url_public", ""),
                "status": "published",
            }

        metadata["figshare_doi"] = result["figshare_doi"]
        metadata.setdefault("platform_status", {})[self.platform] = result
        return result
