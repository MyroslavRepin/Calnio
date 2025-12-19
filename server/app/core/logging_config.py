import os

from loguru import logger
import sys
import logging

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Configure Loguru: short tracebacks, clear format
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
           backtrace=False, diagnose=False, colorize=True)


# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# LOG_DIR = os.path.join(BASE_DIR, "..", "..", "logs")  # logs рядом с проектом
# os.makedirs(LOG_DIR, exist_ok=True)

# Note: path to save logs are located in main.py

# Optionally, set log level here
logger.level("INFO")

# Export logger for use in other modules
__all__ = ["logger"]



