"""Path resolution utilities for nested data structures."""

import copy
from typing import Any, Dict, Union

from pyrsistent import PMap, pmap

from .exceptions import PathResolutionError
from .logging import get_logger

logger = get_logger("path_resolver")


def _set_on_object(obj: Any, key: str, value: Any) -> Any:
    """Set a value on an object using the most appropriate method.

    Tries different approaches in order:
    1. __setitem__() for dict-like objects (preferred for consistency)
    2. setattr() for objects with attributes
    3. Convert to dict as last resort

    Args:
        obj: The object to set the value on
        key: The key/attribute name
        value: The value to set

    Returns:
        The updated object (may be a modified copy or dict conversion)
    """
    # Try __setitem__ first for dict-like objects
    # This is preferred because it maintains the expected behavior
    # for objects that act like dicts
    if hasattr(obj, "__setitem__"):
        try:
            obj_copy = copy.deepcopy(obj)
            obj_copy[key] = value
            logger.debug(
                f"Set item '{key}' on {type(obj).__name__} object using __setitem__"
            )
            return obj_copy
        except (TypeError, KeyError, AttributeError):
            # __setitem__ failed, fall through to try setattr
            pass

    # Try setattr for objects with attributes
    try:
        # Create a deep copy of the object to maintain immutability
        # Use deepcopy to avoid sharing mutable attributes
        obj_copy = copy.deepcopy(obj)
        setattr(obj_copy, key, value)
        logger.debug(
            f"Set attribute '{key}' on {type(obj).__name__} object using setattr"
        )
        return obj_copy
    except (AttributeError, TypeError):
        # setattr failed
        pass

    # Last resort: convert to dict
    logger.warning(
        f"Converting {type(obj).__name__} to dict to set nested path '{key}'. "
        f"Object does not support attribute or item assignment."
    )
    # Try to convert object to dict
    if hasattr(obj, "__dict__"):
        result = copy.deepcopy(obj.__dict__)
    else:
        result = {}
    result[key] = value
    return result


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
                # Try to get attribute from object
                try:
                    current = getattr(current, part)
                except AttributeError:
                    # Try item access as fallback
                    try:
                        current = current[part]
                    except (KeyError, TypeError):
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

        # Get the existing nested value or create a new dict
        nested = data.get(key, {})

        # Handle non-dict/PMap objects with smart object handling
        if not isinstance(nested, (dict, PMap)):
            # For non-dict objects, we need to set the nested path differently
            # First, check if this is the final level (base case for recursion)
            nested_parts = remaining_path.split(".")
            if len(nested_parts) == 1:
                # Direct property/attribute set on the object
                updated_obj = _set_on_object(nested, nested_parts[0], value)
                return data.set(key, updated_obj)
            else:
                # Multi-level nested path on non-dict object
                # Get the next level from the object
                next_key = nested_parts[0]
                next_remaining = ".".join(nested_parts[1:])

                # Try to get the nested attribute/item
                try:
                    # Try attribute access first
                    next_nested = getattr(nested, next_key)
                except AttributeError:
                    try:
                        # Try item access
                        next_nested = nested[next_key]
                    except (KeyError, TypeError):
                        # Attribute/item doesn't exist, create new dict
                        next_nested = {}

                # Recursively handle the next nested value
                if isinstance(next_nested, (dict, PMap)):
                    # Next level is a dict/PMap, use standard recursive logic
                    nested_pmap = (
                        pmap(next_nested)
                        if isinstance(next_nested, dict)
                        else next_nested
                    )
                    updated_next = set_nested_path(nested_pmap, next_remaining, value)
                    # Set the updated dict back on the object
                    updated_obj = _set_on_object(nested, next_key, dict(updated_next))
                else:
                    # Next level is also a non-dict object
                    # Create a temporary PMap to hold just this object
                    temp_pmap = pmap({next_key: next_nested})
                    # Recursively set on the nested object
                    updated_temp = set_nested_path(
                        temp_pmap, f"{next_key}.{next_remaining}", value
                    )
                    # Extract the updated nested object
                    updated_next_obj = updated_temp[next_key]
                    # Set it back on the parent object
                    updated_obj = _set_on_object(nested, next_key, updated_next_obj)

                return data.set(key, updated_obj)

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
