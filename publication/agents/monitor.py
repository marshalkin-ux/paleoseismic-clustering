"""Agent 8 — Publication monitoring and status aggregation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger

from publication.utils.metadata import save_metadata
from publication.utils.report import render_report


class MonitorAgent:
    platform = "monitor"

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or Path(__file__).resolve().parents[1] / "output"

    def generate_report(self, metadata: dict[str, Any]) -> Path:
        report_path = self.output_dir / "report.html"
        render_report(metadata, report_path, metadata.get("platform_status"))
        save_metadata(self.output_dir / "master_metadata.json", metadata)
        logger.info("Report written to {}", report_path)
        return report_path

    def status_summary(self, metadata: dict[str, Any]) -> dict[str, Any]:
        platforms = metadata.get("platform_status", {})
        summary = {
            "doi": metadata.get("doi"),
            "platforms_completed": sum(
                1 for p in platforms.values() if isinstance(p, dict) and p.get("status") in ("published", "submitted")
            ),
            "platforms_total": len(platforms),
            "pending_manual": [],
        }
        for name, info in platforms.items():
            if isinstance(info, dict) and info.get("status") in ("manual_pending", "skipped_mock", "pending"):
                summary["pending_manual"].append(name)
        return summary
