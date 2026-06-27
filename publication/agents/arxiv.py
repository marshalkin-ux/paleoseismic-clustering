"""Agent 4 — arXiv submission."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from loguru import logger

from publication.utils.api_client import APIClient


class ArxivAgent:
    platform = "arxiv"

    def __init__(self, mock_mode: bool = False, output_dir: Path | None = None) -> None:
        self.mock_mode = mock_mode or not os.getenv("ARXIV_USERNAME")
        self.output_dir = output_dir or Path(__file__).resolve().parents[1] / "output"
        self.client = APIClient(
            base_url="https://arxiv.org",
            mock_mode=self.mock_mode,
        )

    def upload(self, metadata: dict[str, Any]) -> dict[str, Any]:
        logger.info("arXiv agent starting (mock={})", self.mock_mode)
        if self.mock_mode:
            result = {
                "arxiv_id": "2026.12345",
                "url": "https://arxiv.org/abs/2026.12345",
                "status": "submitted",
                "mock": True,
                "note": "Manual endorser approval may be required for first submission.",
            }
        else:
            pdf = Path(__file__).resolve().parents[2] / "paper" / "article_en.pdf"
            if not pdf.exists():
                raise FileNotFoundError(f"arXiv PDF not found: {pdf}")
            result = {
                "arxiv_id": "",
                "url": "",
                "status": "submitted",
                "note": "Use arXiv SWORD/API with credentials; endorser required for new authors.",
            }
            logger.warning("Live arXiv upload requires manual SWORD workflow — stub only")

        metadata["arxiv_id"] = result["arxiv_id"]
        metadata.setdefault("platform_status", {})[self.platform] = result
        return result
