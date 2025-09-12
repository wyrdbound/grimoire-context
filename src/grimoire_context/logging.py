"""
Logging utilities for grimoire-context.

This module provides a centralized logger for the grimoire-context library using
grimoire-logging for flexible dependency injection support.
Applications can inject custom logger implementations or configure standard logging.
"""

from typing import Optional

from grimoire_logging import (  # type: ignore[import-untyped]
    LoggerProtocol,
    clear_logger_injection,
    inject_logger,
)
from grimoire_logging import get_logger as _get_logger  # type: ignore[import-untyped]

# Library-wide logger using grimoire-logging namespace
logger = _get_logger("grimoire_context")


def get_logger(name: Optional[str] = None) -> LoggerProtocol:
    """Get a logger instance for the given name or return the main logger.

    Args:
        name: Optional name for a child logger (e.g., "context", "merge").
              If None, returns the main grimoire_context logger.

    Returns:
        Logger instance that conforms to LoggerProtocol
    """
    if name is None:
        return logger

    # Create child logger with grimoire_context namespace
    full_name = f"grimoire_context.{name}" if name else "grimoire_context"
    return _get_logger(full_name)


# Re-export grimoire-logging functions for convenience
__all__ = [
    "logger",
    "get_logger",
    "inject_logger",
    "clear_logger_injection",
    "LoggerProtocol",
]
