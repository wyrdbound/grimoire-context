"""Wyrdbound Context Package.

Immutable, hierarchical context management for the Wyrdbound tabletop RPG engine.

This package provides a flexible context management solution that supports:
- Immutable operations with copy-on-write semantics
- Hierarchical scoping with variable shadowing
- Dict-like interface for easy usage
- Template resolution integration
- Parallel execution support

Example usage:
    >>> from wyrdbound_context import WyrdboundContext
    >>> context = WyrdboundContext({'player': 'Alice', 'hp': 100})
    >>> new_context = context.set_variable('hp', 90)
    >>> print(context['hp'])  # 100 (original unchanged)
    >>> print(new_context['hp'])  # 90 (new version)
"""

from .context import WyrdboundContext
from .exceptions import (
    ContextMergeError,
    InvalidContextOperation,
    PathResolutionError,
    TemplateError,
    WyrdboundContextError,
)
from .merge import ContextMerger
from .protocols import TemplateResolver

__version__ = "0.1.0"
__author__ = "Wyrdbound Team"
__email__ = "team@wyrdbound.com"

__all__ = [
    # Main classes
    "WyrdboundContext",
    "ContextMerger",
    # Protocols
    "TemplateResolver",
    # Exceptions
    "WyrdboundContextError",
    "TemplateError",
    "ContextMergeError",
    "PathResolutionError",
    "InvalidContextOperation",
    # Metadata
    "__version__",
]
