"""Grimoire Context Package.

Immutable, hierarchical context management for the Grimoire tabletop RPG engine.

This package provides a flexible context management solution that supports:
- Immutable operations with copy-on-write semantics
- Hierarchical scoping with variable shadowing
- Dict-like interface for easy usage
- Template resolution integration
- Parallel execution support

Example usage:
    >>> from grimoire_context import GrimoireContext
    >>> context = GrimoireContext({'player': 'Alice', 'hp': 100})
    >>> new_context = context.set_variable('hp', 90)
    >>> print(context['hp'])  # 100 (original unchanged)
    >>> print(new_context['hp'])  # 90 (new version)
"""

from .context import GrimoireContext
from .exceptions import (
    ContextMergeError,
    GrimoireContextError,
    InvalidContextOperation,
    PathResolutionError,
    TemplateError,
)
from .logging import LoggerProtocol, clear_logger_injection, get_logger, inject_logger
from .merge import ContextMerger
from .protocols import TemplateResolver

__version__ = "0.1.1"
__author__ = "Grimoire Team"
__email__ = "team@grimoire.com"

__all__ = [
    # Main classes
    "GrimoireContext",
    "ContextMerger",
    # Protocols
    "TemplateResolver",
    # Logging
    "get_logger",
    "inject_logger",
    "clear_logger_injection",
    "LoggerProtocol",
    # Exceptions
    "GrimoireContextError",
    "TemplateError",
    "ContextMergeError",
    "PathResolutionError",
    "InvalidContextOperation",
    # Metadata
    "__version__",
]
