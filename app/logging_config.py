"""Logging configuration module."""

from logging.handlers import RotatingFileHandler
from pathlib import Path
import logging
import sys

from app.config import settings

_configured = False


def setup_logging() -> None:
    """Configure console and rotating file logging for the application."""
    global _configured
    if _configured:
        return

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    log_format = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    formatter = logging.Formatter(log_format)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Console handler (always attached)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Rotating file handler (logs/app.log, 1 MB, 3 backups)
    log_dir = settings.base_dir / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=1_048_576,  # 1 MB
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except OSError as err:
        root_logger.warning("Failed to initialize file logger (%s); using console only", err)

    _configured = True
