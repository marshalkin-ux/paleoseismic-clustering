"""Agent 2 — Zenodo deposition and DOI registration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from loguru import logger

from publication.utils.api_client import APIClient


class ZenodoAgent:
    platform = "zenodo"

    def __init__(self, mock_mode: bool = False, output_dir: Path | None = None) -> None:
        self.mock_mode = mock_mode or not os.getenv("ZENODO_ACCESS_TOKEN")
        self.output_dir = output_dir or Path(__file__).resolve().parents[1] / "output"
        use_sandbox = os.getenv("ZENODO_USE_SANDBOX", "true").lower() == "true"
        base = (
            "https://sandbox.zenodo.org/api"
            if use_sandbox
            else "https://zenodo.org/api"
        )
        self.client = APIClient(
            base_url=base,
            token=os.getenv("ZENODO_ACCESS_TOKEN"),
            token_prefix="Bearer ",
            mock_mode=self.mock_mode,
        )

    def upload(self, metadata: dict[str, Any]) -> dict[str, Any]:
        logger.info("Zenodo agent starting (mock={})", self.mock_mode)
        if self.mock_mode:
            result = {
                "doi": "10.5281/zenodo.1234567",
                "zenodo_url": "https://zenodo.org/record/1234567",
                "status": "published",
                "mock": True,
            }
        else:
            deposition = self.client.request(
                "POST",
                "/deposit/depositions",
                json={
                    "metadata": {
                        "title": metadata["title_en"],
                        "description": metadata["abstract_en"],
                        "creators": [{"name": a["name_en"]} for a in metadata.get("authors", [])],
                        "keywords": metadata.get("keywords_en", []),
                        "license": "mit",
                    }
                },
            )
            dep_id = deposition["id"]
            supp = self.output_dir / "supplementary.zip"
            if supp.exists():
                with supp.open("rb") as fh:
                    self.client.request(
                        "POST",
                        f"/deposit/depositions/{dep_id}/files",
                        data={"name": supp.name},
                        files={"file": fh},
                    )
            published = self.client.request("POST", f"/deposit/depositions/{dep_id}/actions/publish")
            result = {
                "doi": published.get("doi", ""),
                "zenodo_url": published.get("links", {}).get("record_html", ""),
                "status": "published",
            }

        metadata["doi"] = result["doi"]
        metadata["zenodo_url"] = result["zenodo_url"]
        metadata.setdefault("platform_status", {})[self.platform] = result
        logger.info("Zenodo DOI: {}", result["doi"])
        return result
