"""Path resolution utilities for nested data structures."""

from typing import Any, Dict, Union

from pyrsistent import PMap, pmap

from .exceptions import PathResolutionError
from .logging import get_logger

logger = get_logger("path_resolver")


def get_nested_path(
    data: Union[Dict[str, Any], PMap], path: str, default: Any = None
) -> Any:
    """Get value from nested dict using dot notation.

    Args:
        data: Dictionary or PMap to search in
        path: Dot-separated path (e.g., 'variables.character.hp')
        default: Value to return if path is not found

    Returns:
        The value at the specified path, or default if not found

    Examples:
        >>> data = {'variables': {'character': {'hp': 50}}}
        >>> get_nested_path(data, 'variables.character.hp')
        50
        >>> get_nested_path(data, 'variables.missing', 'default')
        'default'
    """
    if not path:
        return data

    try:
        current = data
        for part in path.split("."):
            if isinstance(current, (dict, PMap)):
                current = current[part]
            else:
                # Current value is not a dict/mapping, can't traverse further
                return default
        return current
    except (KeyError, TypeError, AttributeError):
        return default


def set_nested_path(data: PMap[str, Any], path: str, value: Any) -> PMap[str, Any]:
    """Set value in nested immutable structure using dot notation.

    Args:
        data: Immutable PMap to update
        path: Dot-separated path (e.g., 'variables.character.hp')
        value: Value to set at the path

    Returns:
        New PMap with the value set at the specified path

    Raises:
        PathResolutionError: If the path cannot be resolved

    Examples:
        >>> data = pmap({'variables': {'character': {'hp': 50}}})
        >>> new_data = set_nested_path(data, 'variables.character.hp', 60)
        >>> new_data['variables']['character']['hp']
        60
    """
    if not path:
        raise PathResolutionError("Cannot set value with empty path")

    try:
        parts = path.split(".")
        if len(parts) == 1:
            # Simple case: set at root level
            logger.debug(f"Setting root-level variable '{parts[0]}'")
            return data.set(parts[0], value)

        logger.debug(f"Setting nested path '{path}' with {len(parts)} levels")

        # Handle nested path
        key = parts[0]
        remaining_path = ".".join(parts[1:])

        # Get or create nested dict
        nested = data.get(key, {})
        if not isinstance(nested, (dict, PMap)):
            # Overwrite non-dict value with new nested structure
            logger.warning(
                f"Overwriting non-dict value at '{key}' to create nested path '{path}'"
            )
            nested = {}

        # Convert to PMap if needed and recursively set
        nested_pmap = pmap(nested) if isinstance(nested, dict) else nested
        updated_nested = set_nested_path(nested_pmap, remaining_path, value)

        # Convert back to dict for storage
        return data.set(key, dict(updated_nested))

    except Exception as e:
        logger.error(f"Failed to set nested path '{path}': {e}")
        raise PathResolutionError(f"Failed to set path '{path}': {e}") from e


def has_nested_path(data: Union[Dict[str, Any], PMap], path: str) -> bool:
    """Check if a nested path exists in the data structure.

    Args:
        data: Dictionary or PMap to check
        path: Dot-separated path to check

    Returns:
        True if the path exists, False otherwise

    Examples:
        >>> data = {'variables': {'character': {'hp': 50}}}
        >>> has_nested_path(data, 'variables.character.hp')
        True
        >>> has_nested_path(data, 'variables.missing')
        False
    """
    if not path:
        return True

    try:
        current = data
        for part in path.split("."):
            if isinstance(current, (dict, PMap)) and part in current:
                current = current[part]
            else:
                return False
        return True
    except (KeyError, TypeError, AttributeError):
        return False


def delete_nested_path(data: PMap[str, Any], path: str) -> PMap[str, Any]:
    """Delete a value at a nested path from an immutable structure.

    Args:
        data: Immutable PMap to update
        path: Dot-separated path to delete

    Returns:
        New PMap with the path removed

    Raises:
        PathResolutionError: If the path cannot be resolved or deleted

    Examples:
        >>> data = pmap({'variables': {'character': {'hp': 50, 'mp': 30}}})
        >>> new_data = delete_nested_path(data, 'variables.character.hp')
        >>> 'hp' in new_data['variables']['character']
        False
    """
    if not path:
        raise PathResolutionError("Cannot delete with empty path")

    try:
        parts = path.split(".")
        if len(parts) == 1:
            # Simple case: delete at root level
            if parts[0] not in data:
                raise PathResolutionError(f"Key '{parts[0]}' not found")
            return data.discard(parts[0])

        # Handle nested path
        key = parts[0]
        remaining_path = ".".join(parts[1:])

        if key not in data:
            raise PathResolutionError(f"Key '{key}' not found in path '{path}'")

        nested = data[key]
        if not isinstance(nested, (dict, PMap)):
            raise PathResolutionError(
                f"Cannot traverse non-dict value at '{key}' in path '{path}'"
            )

        # Convert to PMap if needed and recursively delete
        nested_pmap = pmap(nested) if isinstance(nested, dict) else nested
        updated_nested = delete_nested_path(nested_pmap, remaining_path)

        # Convert back to dict for storage
        return data.set(key, dict(updated_nested))

    except PathResolutionError:
        raise
    except Exception as e:
        raise PathResolutionError(f"Failed to delete path '{path}': {e}") from e
