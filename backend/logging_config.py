import os
import sys
from pathlib import Path
from loguru import logger


def setup_logging():
    """Configure loguru logging for the application."""
    # Remove default handler
    logger.remove()

    # Console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
        colorize=True,
    )

    # File handler with rotation
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    logger.add(
        str(log_dir / "app_{time:YYYY-MM-DD}.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
    )

    # Error file handler
    logger.add(
        str(log_dir / "error_{time:YYYY-MM-DD}.log"),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
    )

    return logger
