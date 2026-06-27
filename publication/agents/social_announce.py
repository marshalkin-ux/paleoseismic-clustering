"""Optional social announcement stubs (Twitter/X, LinkedIn, Telegram)."""

from __future__ import annotations

from typing import Any

from loguru import logger


class SocialAnnounceAgent:
    """Stub announcements — configure API tokens in .env for live posting."""

    def announce(self, metadata: dict[str, Any], dry_run: bool = True) -> dict[str, str]:
        message = (
            f"New publication: {metadata.get('title_en', '')}\n"
            f"DOI: {metadata.get('doi') or 'pending'}\n"
            f"{metadata.get('github_url', '')}"
        )
        results = {}
        for platform in ("twitter", "linkedin", "telegram"):
            if dry_run:
                results[platform] = f"stub: would post — {message[:80]}..."
                logger.info("[{}] stub announcement", platform)
            else:
                results[platform] = "not_implemented — add API integration"
        metadata.setdefault("platform_status", {})["social_announce"] = results
        return results
