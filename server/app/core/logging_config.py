from loguru import logger
import sys

# Configure Loguru: short tracebacks, clear format
logger.remove()
logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
           backtrace=False, diagnose=False, colorize=True)

# Optionally, set log level here
logger.level("INFO")

# Export logger for use in other modules
__all__ = ["logger"]

