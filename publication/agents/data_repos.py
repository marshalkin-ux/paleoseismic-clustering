"""Agent 6 — PANGAEA, GFZ, and Dryad data repositories."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from loguru import logger

from publication.utils.api_client import APIClient


class DataReposAgent:
    """Upload to geoscience data repositories with moderation polling."""

    PLATFORMS = ("pangaea", "gfz", "dryad")

    ENDPOINTS = {
        "pangaea": "https://ws.pangaea.de/",
        "gfz": "https://dataservices.gfz-potsdam.de/",
        "dryad": "https://datadryad.org/api/v2/",
    }

    def __init__(self, mock_mode: bool = False, output_dir: Path | None = None) -> None:
        self.mock_mode = mock_mode
        self.output_dir = output_dir or Path(__file__).resolve().parents[1] / "output"
        self.clients = {
            name: APIClient(
                base_url=url,
                token=os.getenv(f"{name.upper()}_TOKEN"),
                mock_mode=mock_mode or not os.getenv(f"{name.upper()}_TOKEN"),
            )
            for name, url in self.ENDPOINTS.items()
        }

    def upload_platform(self, platform: str, metadata: dict[str, Any]) -> dict[str, Any]:
        client = self.clients[platform]
        logger.info("{} agent starting (mock={})", platform, client.mock_mode)

        if client.mock_mode:
            mock_doi = {
                "pangaea": "10.1594/PANGAEA.123456",
                "gfz": "10.5880/GFZ.2026.001",
                "dryad": "10.5061/dryad.abc123",
            }[platform]
            result = {
                f"{platform}_doi": mock_doi,
                "status": "published",
                "mock": True,
                "note": f"{platform.upper()} moderation simulated in mock mode.",
            }
        else:
            submission = client.request(
                "POST",
                "datasets",
                json={
                    "title": metadata["title_en"],
                    "abstract": metadata["abstract_en"],
                },
            )
            polled = client.poll_status(
                f"datasets/{submission.get('id', 'unknown')}",
                status_key="status",
                success_values=("published", "complete"),
                pending_values=("pending", "processing", "submitted", "in_review", "moderation"),
            )
            result = {
                f"{platform}_doi": polled.get("doi", ""),
                "status": polled.get("status", "pending"),
            }

        key = f"{platform}_doi"
        metadata[key] = result[key]
        metadata.setdefault("platform_status", {})[platform] = result
        return result

    def upload_all(self, metadata: dict[str, Any], platforms: list[str] | None = None) -> dict[str, dict[str, Any]]:
        selected = platforms or list(self.PLATFORMS)
        results = {}
        for platform in selected:
            if platform in self.PLATFORMS:
                results[platform] = self.upload_platform(platform, metadata)
        return results
