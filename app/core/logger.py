import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler


# Create logs directory relative to project root
LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

log_file = LOG_DIR / "tradebot.log"

logger = logging.getLogger("tradebot")
logger.setLevel(logging.INFO)

# Prevent duplicate handlers on module reload
if not logger.handlers:
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        str(log_file), maxBytes=10**6, backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def log_trade(message: str):
    logger.info(message)


def log_error(message: str):
    logger.error(message)


def log_warning(message: str):
    logger.warning(message)


def log_info(message: str):
    logger.info(message)