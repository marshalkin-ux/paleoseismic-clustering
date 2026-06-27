"""Loguru configuration for publication automation."""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger


def setup_logging(log_dir: Path | None = None, level: str = "INFO") -> Path:
    """Configure loguru; return logs directory path."""
    log_dir = log_dir or Path(__file__).resolve().parents[1] / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    )
    logger.add(
        log_dir / "publication_{time:YYYY-MM-DD}.log",
        rotation="1 day",
        retention="30 days",
        level=level,
        encoding="utf-8",
    )
    return log_dir
