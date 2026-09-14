"""Logging configuration module for File Organizer."""

import logging
from pathlib import Path


def get_logger(
    name: str = "file_organizer",
    log_file: str | Path | None = "file_organizer.log",
    level: int = logging.INFO,
    reset_handlers: bool = False,
) -> logging.Logger:
    """Configures and returns a logger instance with console and file handlers.

    Args:
        name: Name of the logger.
        log_file: Path to the log file. If None, only console logging is used.
        level: Logging level (e.g. logging.INFO, logging.DEBUG).
        reset_handlers: If True, removes existing handlers before configuring.

    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if reset_handlers:
        close_logger_handlers(logger)

    # If logger has no handlers, configure it
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler (if log_file specified)
        if log_file:
            log_path = Path(log_file)
            if log_path.parent:
                log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger


def close_logger_handlers(logger: logging.Logger) -> None:
    """Closes and removes all handlers attached to a logger to release file locks."""
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)
