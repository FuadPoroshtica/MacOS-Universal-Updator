"""Logging configuration and utilities."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_log_directory() -> Path:
    """Get the directory for storing logs."""
    log_dir = Path.home() / ".macos-updater" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logger(name: str = "updater", level: int = logging.INFO) -> logging.Logger:
    """Set up and configure the application logger."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(level)

    # File handler with daily rotation
    log_file = get_log_directory() / f"updater_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler (minimal for TUI compatibility)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str = "updater") -> logging.Logger:
    """Get an existing logger or create a new one."""
    return logging.getLogger(name)


def get_recent_logs(lines: int = 100) -> list[str]:
    """Get the most recent log entries."""
    log_dir = get_log_directory()
    today_log = log_dir / f"updater_{datetime.now().strftime('%Y%m%d')}.log"

    if not today_log.exists():
        return []

    with open(today_log, "r") as f:
        all_lines = f.readlines()
        return all_lines[-lines:] if len(all_lines) > lines else all_lines


def clear_old_logs(days: int = 30) -> int:
    """Remove log files older than specified days. Returns number of files removed."""
    log_dir = get_log_directory()
    removed = 0
    cutoff = datetime.now().timestamp() - (days * 86400)

    for log_file in log_dir.glob("updater_*.log"):
        if log_file.stat().st_mtime < cutoff:
            log_file.unlink()
            removed += 1

    return removed
