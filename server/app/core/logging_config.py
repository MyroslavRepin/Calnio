import os

from loguru import logger
import sys
import logging

os.makedirs("/calnio/logs", exist_ok=True)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Configure Loguru: short tracebacks, clear format
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
           backtrace=False, diagnose=False, colorize=True)

# Saving logs to file
os.makedirs("/calnio/logs", exist_ok=True)

# File - full traceback
logger.add("/calnio/logs/app_{time:YYYY-MM-DD}.log",
           rotation="1 day",
           retention="14 days",
           compression="zip",
           format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
           level="DEBUG",
           backtrace=True,
           diagnose=True)

# Optionally, set log level here
logger.level("INFO")

# Export logger for use in other modules
__all__ = ["logger"]

