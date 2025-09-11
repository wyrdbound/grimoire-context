"""Custom exceptions for Grimoire Context package."""


class GrimoireContextError(Exception):
    """Base exception for all Grimoire Context errors."""

    pass


class TemplateError(GrimoireContextError):
    """Raised when template resolution fails."""

    pass


class ContextMergeError(GrimoireContextError):
    """Raised when context merging fails due to conflicts or other issues."""

    pass


class PathResolutionError(GrimoireContextError):
    """Raised when path resolution fails."""

    pass


class InvalidContextOperation(GrimoireContextError):
    """Raised when an invalid operation is attempted on a context."""

    pass
