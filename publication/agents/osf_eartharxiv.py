"""Agent 5 — OSF and EarthArXiv preprint upload."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from loguru import logger

from publication.utils.api_client import APIClient


class OSFEarthArxivAgent:
    platform = "osf"

    def __init__(self, mock_mode: bool = False, output_dir: Path | None = None) -> None:
        self.mock_mode = mock_mode or not os.getenv("OSF_TOKEN")
        self.output_dir = output_dir or Path(__file__).resolve().parents[1] / "output"
        self.client = APIClient(
            base_url="https://api.osf.io/v2",
            token=os.getenv("OSF_TOKEN"),
            mock_mode=self.mock_mode,
        )

    def upload(self, metadata: dict[str, Any]) -> dict[str, Any]:
        logger.info("OSF/EarthArXiv agent starting (mock={})", self.mock_mode)
        if self.mock_mode:
            result = {
                "osf_url": "https://osf.io/abc12/",
                "eartharxiv_url": "https://eartharxiv.org/repository/view/1234/",
                "status": "published",
                "mock": True,
            }
        else:
            project_id = os.getenv("OSF_PROJECT_ID", "")
            preprint = self.client.request(
                "POST",
                "/preprints/",
                json={
                    "data": {
                        "type": "preprints",
                        "attributes": {
                            "title": metadata["title_en"],
                            "description": metadata["abstract_en"],
                        },
                    }
                },
            )
            result = {
                "osf_url": f"https://osf.io/{project_id}/" if project_id else "",
                "eartharxiv_url": preprint.get("data", {}).get("links", {}).get("html", ""),
                "status": "published",
            }

        metadata["osf_url"] = result["osf_url"]
        metadata["eartharxiv_url"] = result["eartharxiv_url"]
        metadata.setdefault("platform_status", {})[self.platform] = result
        return result
