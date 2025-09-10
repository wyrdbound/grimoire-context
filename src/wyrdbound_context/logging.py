"""Logging utilities with dependency injection support."""

import logging
from typing import Dict, Optional, Protocol


class LoggerProtocol(Protocol):
    """Protocol defining the logger interface for dependency injection."""

    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log debug message."""
        ...

    def info(self, msg: str, *args, **kwargs) -> None:
        """Log info message."""
        ...

    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log warning message."""
        ...

    def error(self, msg: str, *args, **kwargs) -> None:
        """Log error message."""
        ...

    def critical(self, msg: str, *args, **kwargs) -> None:
        """Log critical message."""
        ...


class LoggerProxy:
    """Proxy that delegates to injected logger or falls back to standard logging."""

    def __init__(self, name: str):
        self._name = name
        module_name = name.split(".")[-1] if "." in name else name
        self._fallback_logger = logging.getLogger(module_name)

    def _get_current_logger(self) -> LoggerProtocol:
        """Get the current active logger (injected or fallback)."""
        global _injected_logger
        return (
            _injected_logger if _injected_logger is not None else self._fallback_logger
        )

    def debug(self, msg: str, *args, **kwargs) -> None:
        self._get_current_logger().debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        self._get_current_logger().info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self._get_current_logger().warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self._get_current_logger().error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        self._get_current_logger().critical(msg, *args, **kwargs)


# Global logger instance for injection
_injected_logger: Optional[LoggerProtocol] = None
_logger_instances: Dict[str, LoggerProxy] = {}


def inject_logger(logger: Optional[LoggerProtocol]) -> None:
    """Inject a custom logger implementation.

    Args:
        logger: Logger implementation that conforms to LoggerProtocol,
                or None to revert to standard logging
    """
    global _injected_logger
    _injected_logger = logger


def clear_logger_injection() -> None:
    """Clear any injected logger and revert to default."""
    inject_logger(None)


def get_logger(name: str) -> LoggerProtocol:
    """Get a logger instance for the given name.

    Returns a logger proxy that automatically delegates to the current
    injected logger or falls back to standard Python logging.

    Args:
        name: Name for the logger (typically __name__)

    Returns:
        Logger proxy that conforms to LoggerProtocol
    """
    if name in _logger_instances:
        return _logger_instances[name]

    # Create a new proxy for this name
    proxy = LoggerProxy(name)
    _logger_instances[name] = proxy
    return proxy
