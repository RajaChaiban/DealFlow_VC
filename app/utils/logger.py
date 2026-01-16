"""
Logging configuration using Loguru.

Provides colorized console output and rotating file logs.
"""

import sys
from pathlib import Path

from loguru import logger

# Remove default handler
logger.remove()

# Log format
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# Console handler (colorized)
logger.add(
    sys.stdout,
    format=LOG_FORMAT,
    level="INFO",
    colorize=True,
    backtrace=True,
    diagnose=True,
)

# File handler (with rotation)
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logger.add(
    log_dir / "app.log",
    format=LOG_FORMAT,
    level="DEBUG",
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    backtrace=True,
    diagnose=True,
    enqueue=True,  # Thread-safe logging
)

# Export the configured logger
__all__ = ["logger"]
