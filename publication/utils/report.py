"""Generate HTML publication status report."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape


def render_report(metadata: dict[str, Any], output_path: Path, platforms: dict[str, Any] | None = None) -> Path:
    templates_dir = Path(__file__).resolve().parents[1] / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report_template.html.j2")
    html = template.render(
        metadata=metadata,
        platforms=platforms or metadata.get("platform_status", {}),
        generated_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path
