from __future__ import annotations

import logging
import sys
from pathlib import Path

from rich.logging import RichHandler


def setup_logging(log_file: Path | None = None, level: int = logging.INFO) -> None:
    """Configure application logging with Rich console output and optional file output."""
    handlers: list[logging.Handler] = [
        RichHandler(rich_tracebacks=True, show_path=False)
    ]

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%H:%M:%S]",
        handlers=handlers,
        force=True,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
