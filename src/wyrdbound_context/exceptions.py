"""Custom exceptions for Wyrdbound Context package."""


class WyrdboundContextError(Exception):
    """Base exception for all Wyrdbound Context errors."""

    pass


class TemplateError(WyrdboundContextError):
    """Raised when template resolution fails."""

    pass


class ContextMergeError(WyrdboundContextError):
    """Raised when context merging fails due to conflicts or other issues."""

    pass


class PathResolutionError(WyrdboundContextError):
    """Raised when path resolution fails."""

    pass


class InvalidContextOperation(WyrdboundContextError):
    """Raised when an invalid operation is attempted on a context."""

    pass
