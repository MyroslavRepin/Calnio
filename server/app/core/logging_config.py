from loguru import logger
import sys
from pathlib import Path

logger.remove()

logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

logger.add(
    sys.stdout,
    format=log_format,
    backtrace=False,
    diagnose=False,
    colorize=True,
    level="DEBUG"
)

logger.add(
    logs_dir / "app.log",
    format=log_format,
    backtrace=True,
    diagnose=True,
    colorize=False,
    level="DEBUG",
    rotation="00:00",
    retention="7 days",
    compression="zip",
    encoding="utf-8"
)

logger.add(
    logs_dir / "error.log",
    format=log_format,
    backtrace=True,
    diagnose=True,
    colorize=False,
    level="ERROR",
    rotation="50 MB",
    retention="30 days",
    compression="zip",
    encoding="utf-8"
)

logger.level("DEBUG")

__all__ = ["logger"]

