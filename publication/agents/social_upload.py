"""Agent 7 — ResearchGate and Academia.edu uploads via Selenium."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from loguru import logger


class SocialUploadAgent:
    """
    Browser automation for ResearchGate and Academia.edu.

    IMPORTANT: These platforms require manual login and CAPTCHA solving.
    Set SELENIUM_HEADLESS=false and complete authentication interactively.
    """

    PLATFORMS = ("researchgate", "academia")

    def __init__(self, mock_mode: bool = False, output_dir: Path | None = None) -> None:
        self.mock_mode = mock_mode or os.getenv("SOCIAL_UPLOAD_LIVE", "false").lower() != "true"
        self.output_dir = output_dir or Path(__file__).resolve().parents[1] / "output"

    def _run_selenium_upload(self, platform: str, metadata: dict[str, Any]) -> dict[str, Any]:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
        except ImportError as exc:
            raise ImportError(
                "Install selenium and webdriver-manager for live social uploads"
            ) from exc

        options = Options()
        if os.getenv("SELENIUM_HEADLESS", "false").lower() == "true":
            options.add_argument("--headless=new")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        try:
            urls = {
                "researchgate": "https://www.researchgate.net/",
                "academia": "https://www.academia.edu/upload",
            }
            driver.get(urls[platform])
            logger.warning(
                "Complete {} login/CAPTCHA manually, then press Enter in terminal.",
                platform,
            )
            return {"status": "manual_pending", "url": driver.current_url}
        finally:
            driver.quit()

    def upload(self, metadata: dict[str, Any]) -> dict[str, Any]:
        logger.info("Social upload agent starting (mock={})", self.mock_mode)
        results: dict[str, Any] = {}

        for platform in self.PLATFORMS:
            if self.mock_mode:
                results[platform] = {
                    "status": "skipped_mock",
                    "note": "Requires Selenium + manual CAPTCHA/login. Set SOCIAL_UPLOAD_LIVE=true.",
                }
            else:
                results[platform] = self._run_selenium_upload(platform, metadata)

        metadata["researchgate_status"] = results.get("researchgate", {}).get("status", "pending")
        metadata["academia_status"] = results.get("academia", {}).get("status", "pending")
        metadata.setdefault("platform_status", {})["social_upload"] = results
        return results
