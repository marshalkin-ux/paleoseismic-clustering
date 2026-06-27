#!/usr/bin/env python3
"""CLI entry point for publication automation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from publication.agents.orchestrator import Orchestrator
from publication.utils.logging_config import setup_logging


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scientific publication automation — Zenodo, Figshare, arXiv, OSF, data repos.",
    )
    parser.add_argument(
        "--platforms",
        type=str,
        default="",
        help="Comma-separated platform IDs (zenodo,figshare,osf,pangaea,gfz,dryad,arxiv,social)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Simulate all API calls with mock DOIs")
    parser.add_argument(
        "--prepare-only",
        action="store_true",
        help="Only build metadata and zip packages",
    )
    parser.add_argument("--skip-social", action="store_true", help="Skip ResearchGate/Academia and announcements")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: publication/output)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    pub_dir = Path(__file__).resolve().parent
    setup_logging(pub_dir / "logs")

    platforms = [p.strip() for p in args.platforms.split(",") if p.strip()] or None
    orchestrator = Orchestrator(
        dry_run=args.dry_run,
        prepare_only=args.prepare_only,
        skip_social=args.skip_social,
        platforms=platforms,
        output_dir=args.output_dir,
    )
    metadata = orchestrator.run()
    doi = metadata.get("doi") or "pending"
    print(f"Publication flow complete. DOI: {doi}")
    print(f"Report: {orchestrator.output_dir / 'report.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
