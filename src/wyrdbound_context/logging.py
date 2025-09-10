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


# Global logger instance for injection
_injected_logger: Optional[LoggerProtocol] = None
_logger_instances: Dict[str, LoggerProtocol] = {}


def inject_logger(logger: Optional[LoggerProtocol]) -> None:
    """Inject a custom logger implementation.

    Args:
        logger: Logger implementation that conforms to LoggerProtocol,
                or None to revert to standard logging
    """
    global _injected_logger, _logger_instances
    _injected_logger = logger

    # Update all existing logger instances
    for name in _logger_instances:
        if logger is not None:
            _logger_instances[name] = logger
        else:
            # Revert to standard logger
            module_name = name.split(".")[-1] if "." in name else name
            _logger_instances[name] = logging.getLogger(module_name)

    # Also update module-level loggers by patching the modules
    import sys

    for module_name, module in sys.modules.items():
        if module_name.startswith("wyrdbound_context.") and hasattr(module, "logger"):
            try:
                if logger is not None:
                    module.logger = logger  # type: ignore[attr-defined]
                else:
                    # Revert to standard logger
                    name = module_name.split(".")[-1]
                    module.logger = logging.getLogger(name)  # type: ignore[attr-defined]
            except (AttributeError, TypeError):
                # Module doesn't support attribute assignment, skip
                pass


def clear_logger_injection() -> None:
    """Clear any injected logger and revert to default."""
    inject_logger(None)


def get_logger(name: str) -> LoggerProtocol:
    """Get a logger instance for the given name.

    If a logger has been injected, returns that logger.
    Otherwise, returns a standard Python logger.

    Args:
        name: Name for the logger (typically __name__)

    Returns:
        Logger instance that conforms to LoggerProtocol
    """
    if name in _logger_instances:
        return _logger_instances[name]

    if _injected_logger is not None:
        _logger_instances[name] = _injected_logger
        return _injected_logger
    else:
        # Return standard Python logger with just the module name
        module_name = name.split(".")[-1] if "." in name else name
        std_logger = logging.getLogger(module_name)
        _logger_instances[name] = std_logger
        return std_logger
