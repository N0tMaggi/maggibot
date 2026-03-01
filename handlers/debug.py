import logging
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.getenv("LOG_DIR", "logs")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DEBUG_MODE = os.getenv("DEBUG_MODE", "FALSE").upper() == "TRUE"


def _ensure_log_dir() -> None:
    os.makedirs(LOG_DIR, exist_ok=True)


def _create_file_handler(path: str) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        path,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(formatter)
    return handler


def _get_logger(name: str, filename: str) -> logging.Logger:
    _ensure_log_dir()
    logger = logging.getLogger(name)

    level = getattr(logging, LOG_LEVEL, logging.INFO)
    logger.setLevel(level)

    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        logger.addHandler(_create_file_handler(os.path.join(LOG_DIR, filename)))

    # Optional console output for local debugging.
    if DEBUG_MODE and not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        stream = logging.StreamHandler()
        stream.setLevel(level)
        stream.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        logger.addHandler(stream)

    logger.propagate = False
    return logger


_system = _get_logger("system", "system.log")
_network = _get_logger("network", "network.log")
_discord = _get_logger("discord", "discord.log")
_debug = _get_logger("debug", "debug.log")
_error = _get_logger("error", "error.log")
_moderation = _get_logger("moderation", "moderation.log")


def LogSystem(message: str) -> None:
    _system.info(message)


def LogDebug(message: str) -> None:
    _debug.info(message)


def LogNetwork(message: str) -> None:
    _network.info(message)


def LogDiscord(message: str) -> None:
    _discord.info(message)


def LogError(message: str) -> None:
    _error.error(message)


def LogModeration(message: str) -> None:
    _moderation.info(message)
