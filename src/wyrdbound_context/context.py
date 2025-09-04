"""Core WyrdboundContext implementation."""

from collections import ChainMap
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    KeysView,
    List,
    Optional,
    Union,
    ValuesView,
)
from uuid import uuid4

try:
    from pyrsistent import PMap, pmap
except ImportError:
    # Fallback type hints if pyrsistent not available
    PMap = Dict  # type: ignore
    pmap = dict  # type: ignore

from .exceptions import InvalidContextOperation, TemplateError
from .path_resolver import (
    delete_nested_path,
    get_nested_path,
    has_nested_path,
    set_nested_path,
)
from .protocols import TemplateResolver


class WyrdboundContext:
    """Immutable, hierarchical context for Wyrdbound flows.

    This class provides a dict-like interface for storing and accessing data
    while maintaining immutability through copy-on-write semantics. It supports
    hierarchical scoping through parent-child relationships and can be used
    with template resolvers for dynamic content resolution.

    Key features:
    - Immutable operations (all modifications return new contexts)
    - Hierarchical scoping with variable shadowing
    - Dict-like interface (__getitem__, __setitem__, etc.)
    - Dot notation path resolution for nested data
    - Template resolution integration
    - Parallel execution support
    """

    def __init__(
        self,
        data: Optional[Union[Dict[str, Any], PMap]] = None,
        parent: Optional["WyrdboundContext"] = None,
        template_resolver: Optional[TemplateResolver] = None,
        context_id: Optional[str] = None,
    ) -> None:
        """Initialize a new WyrdboundContext.

        Args:
            data: Initial data for this context level
            parent: Parent context for hierarchical scoping
            template_resolver: Template resolver for dynamic content
            context_id: Unique identifier for this context
        """
        # Immutable data storage
        if data is None:
            self._data: PMap[str, Any] = pmap({})
        elif isinstance(data, dict):
            self._data = pmap(data)
        else:
            self._data = data

        self._parent: Optional[WyrdboundContext] = parent
        self._template_resolver = template_resolver or (
            parent.template_resolver if parent else None
        )
        self._id: str = context_id or str(uuid4())

        # Hierarchical view (computed on-demand)
        self._chain_view: Optional[ChainMap] = None

    @property
    def template_resolver(self) -> Optional[TemplateResolver]:
        """Get the current template resolver."""
        return self._template_resolver

    @property
    def context_id(self) -> str:
        """Get the unique identifier for this context."""
        return self._id

    @property
    def parent(self) -> Optional["WyrdboundContext"]:
        """Get the parent context."""
        return self._parent

    @property
    def chain_view(self) -> ChainMap:
        """Lazy-loaded hierarchical view of all context levels.

        This creates a ChainMap that provides a unified view of this context
        and all parent contexts, with values in child contexts shadowing
        values in parent contexts.
        """
        if self._chain_view is None:
            if self._parent:
                self._chain_view = ChainMap(dict(self._data), self._parent.chain_view)
            else:
                self._chain_view = ChainMap(dict(self._data))
        return self._chain_view

    def _invalidate_chain_view(self) -> None:
        """Invalidate the cached chain view."""
        self._chain_view = None

    # Dict-like interface
    def __getitem__(self, key: str) -> Any:
        """Get item using dict syntax."""
        return self.chain_view[key]

    def __setitem__(self, key: str, value: Any) -> None:
        """Prevent direct assignment - use immutable methods instead."""
        raise InvalidContextOperation(
            "Direct assignment not allowed. Use set_variable() or update() methods."
        )

    def __contains__(self, key: str) -> bool:
        """Check if key exists in context hierarchy."""
        return key in self.chain_view

    def __iter__(self) -> Iterator[str]:
        """Iterate over keys in context hierarchy."""
        return iter(self.chain_view)

    def __len__(self) -> int:
        """Get number of unique keys in context hierarchy."""
        return len(self.chain_view)

    def __bool__(self) -> bool:
        """Context is truthy if it has any data."""
        return bool(self.chain_view)

    def __eq__(self, other: object) -> bool:
        """Check equality with another context."""
        if not isinstance(other, WyrdboundContext):
            return False
        return dict(self.chain_view) == dict(other.chain_view)

    def __repr__(self) -> str:
        """String representation of the context."""
        return f"WyrdboundContext(id={self._id}, data={dict(self._data)})"

    def keys(self) -> KeysView[str]:
        """Get all keys from context hierarchy."""
        return self.chain_view.keys()

    def values(self) -> ValuesView[Any]:
        """Get all values from context hierarchy."""
        return self.chain_view.values()

    def items(self) -> Iterator[tuple[str, Any]]:
        """Get all key-value pairs from context hierarchy."""
        return iter(self.chain_view.items())

    def get(self, key: str, default: Any = None) -> Any:
        """Get value with optional default."""
        return self.chain_view.get(key, default)

    # Immutable operations
    def set(self, key: str, value: Any) -> "WyrdboundContext":
        """Return new context with updated value at this hierarchical level.

        Args:
            key: Key to set
            value: Value to set

        Returns:
            New WyrdboundContext with the value set
        """
        new_data = self._data.set(key, value)
        return WyrdboundContext(
            new_data,
            self._parent,
            self._template_resolver,
            str(uuid4()),  # Always generate new ID for modified contexts
        )

    def discard(self, key: str) -> "WyrdboundContext":
        """Return new context with key removed from this hierarchical level.

        Args:
            key: Key to remove

        Returns:
            New WyrdboundContext with the key removed
        """
        new_data = self._data.discard(key)
        return WyrdboundContext(
            new_data, self._parent, self._template_resolver, str(uuid4())
        )

    def update(self, updates: Dict[str, Any]) -> "WyrdboundContext":
        """Return new context with multiple updates.

        Args:
            updates: Dictionary of key-value pairs to update

        Returns:
            New WyrdboundContext with all updates applied
        """
        new_data = self._data
        for key, value in updates.items():
            new_data = new_data.set(key, value)
        return WyrdboundContext(
            new_data, self._parent, self._template_resolver, str(uuid4())
        )

    # Hierarchical context management
    def create_child_context(
        self,
        initial_data: Optional[Dict[str, Any]] = None,
        context_id: Optional[str] = None,
    ) -> "WyrdboundContext":
        """Create a new child context with this context as parent.

        Args:
            initial_data: Initial data for the child context
            context_id: Optional custom ID for the child context

        Returns:
            New child WyrdboundContext
        """
        return WyrdboundContext(
            initial_data,
            parent=self,
            template_resolver=self._template_resolver,
            context_id=context_id,
        )

    # Path-based operations
    def set_variable(self, path: str, value: Any) -> "WyrdboundContext":
        """Set value at dot-notation path (e.g., 'outputs.character.hp').

        Args:
            path: Dot-separated path to the variable
            value: Value to set

        Returns:
            New WyrdboundContext with the variable set
        """
        new_data = set_nested_path(self._data, path, value)
        return WyrdboundContext(
            new_data, self._parent, self._template_resolver, str(uuid4())
        )

    def get_variable(self, path: str, default: Any = None) -> Any:
        """Get value at dot-notation path.

        Args:
            path: Dot-separated path to the variable
            default: Default value if path not found

        Returns:
            Value at the path or default
        """
        return get_nested_path(dict(self.chain_view), path, default)

    def has_variable(self, path: str) -> bool:
        """Check if a variable exists at the given path.

        Args:
            path: Dot-separated path to check

        Returns:
            True if the path exists, False otherwise
        """
        return has_nested_path(dict(self.chain_view), path)

    def delete_variable(self, path: str) -> "WyrdboundContext":
        """Delete variable at dot-notation path.

        Args:
            path: Dot-separated path to delete

        Returns:
            New WyrdboundContext with the variable deleted
        """
        new_data = delete_nested_path(self._data, path)
        return WyrdboundContext(
            new_data, self._parent, self._template_resolver, str(uuid4())
        )

    # Template resolution
    def resolve_template(self, template_str: str) -> Any:
        """Resolve template using injected resolver.

        Args:
            template_str: Template string to resolve

        Returns:
            Resolved template result

        Raises:
            TemplateError: If no resolver is configured or resolution fails
        """
        if not self._template_resolver:
            raise TemplateError("No template resolver configured")

        try:
            return self._template_resolver.resolve_template(
                template_str, dict(self.chain_view)
            )
        except Exception as e:
            raise TemplateError(f"Template resolution failed: {e}") from e

    def set_template_resolver(self, resolver: TemplateResolver) -> "WyrdboundContext":
        """Return new context with different template resolver.

        Args:
            resolver: New template resolver to use

        Returns:
            New WyrdboundContext with the resolver set
        """
        return WyrdboundContext(self._data, self._parent, resolver, str(uuid4()))

    # Utility methods
    def to_dict(self) -> Dict[str, Any]:
        """Convert the full context hierarchy to a regular dictionary.

        Returns:
            Dictionary representation of the complete context
        """
        return dict(self.chain_view)

    def local_data(self) -> Dict[str, Any]:
        """Get only the data at this context level (not including parents).

        Returns:
            Dictionary of data only at this hierarchical level
        """
        return dict(self._data)

    def copy(self, new_id: Optional[str] = None) -> "WyrdboundContext":
        """Create a copy of this context with a new ID.

        Args:
            new_id: Optional new ID for the copy

        Returns:
            New WyrdboundContext that is a copy of this one
        """
        return WyrdboundContext(
            self._data, self._parent, self._template_resolver, new_id or str(uuid4())
        )

    # Support for parallel execution (delegated to merge module)
    def execute_parallel(
        self, operations: List[Callable[["WyrdboundContext"], "WyrdboundContext"]]
    ) -> "WyrdboundContext":
        """Execute operations in parallel and return merged result.

        Args:
            operations: List of functions that take a context and return a context

        Returns:
            New WyrdboundContext with merged results from all operations
        """
        from .merge import ContextMerger

        return ContextMerger.execute_parallel_operations(self, operations)
