import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_root_logger():
    # Get the root logger
    logger = logging.getLogger()  # no name => root logger
    logger.setLevel(logging.INFO)

    # Optional: Clear existing handlers (prevents duplicate logs)
    logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    # File Handler
    file_handler = RotatingFileHandler(
        "bot.log", maxBytes=1024 * 1024 * 5, backupCount=5  # 5 MB
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # other:
    logging.getLogger("pyrogram").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    return logger


