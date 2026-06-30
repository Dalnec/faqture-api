import logging
import os
from logging.handlers import RotatingFileHandler


# ANSI color codes for console output
COLORS = {
    'DEBUG':    '\033[36m',   # cyan
    'INFO':     '\033[32m',   # green
    'WARNING':  '\033[33m',   # yellow
    'ERROR':    '\033[31m',   # red
    'CRITICAL': '\033[41m',   # red bg
    'RESET':    '\033[0m',
}

LOG_DIR = 'logs'
LOG_FORMAT = '%(asctime)s [%(levelname)-8s] [%(module)s:%(lineno)d] %(message)s'
LOG_DATE = '%Y-%m-%d %H:%M:%S'
LOG_MAX_BYTES = 5 * 1024 * 1024   # 5 MB
LOG_BACKUP_COUNT = 5


class ColorFormatter(logging.Formatter):
    """Formatter that adds ANSI colors to console output."""

    def format(self, record):
        color = COLORS.get(record.levelname, COLORS['RESET'])
        record.levelname = f"{color}{record.levelname}{COLORS['RESET']}"
        return super().format(record)


def setup_logger(debug=False):
    """Configure the 'faqture' logger with console + file handlers."""
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger('faqture')
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Avoid duplicate handlers on repeated imports
    if logger.handlers:
        return logger

    # --- Console handler (colored) ---
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG if debug else logging.INFO)
    console.setFormatter(ColorFormatter(LOG_FORMAT, datefmt=LOG_DATE))
    logger.addHandler(console)

    # --- General log file (rotating) ---
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'faqture.log'),
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8',
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    logger.addHandler(file_handler)

    # --- Error-only log file (rotating) ---
    error_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'faqture_error.log'),
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8',
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE))
    logger.addHandler(error_handler)

    return logger


def get_logger():
    """Return the configured 'faqture' logger."""
    return logging.getLogger('faqture')


log = get_logger()
