"""Structured logging configuration."""

import logging
import sys
from datetime import datetime


def setup_logging(debug: bool = False) -> logging.Logger:
    """Configure application logging."""
    level = logging.DEBUG if debug else logging.INFO

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    logger = logging.getLogger("dharma_nyaya")
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


logger = setup_logging()
