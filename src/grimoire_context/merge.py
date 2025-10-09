"""Context merging utilities and parallel execution support."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any, Callable, Dict, List

from .exceptions import ContextMergeError
from .logging import get_logger

logger = get_logger("merge")

if TYPE_CHECKING:
    from .context import GrimoireContext


def _get_modification_paths(
    base_data: dict, context_data: dict, prefix: str = ""
) -> set:
    """Get the specific nested paths that were modified between contexts."""
    modified_paths = set()

    # Check for new or modified keys
    for key, value in context_data.items():
        current_path = f"{prefix}.{key}" if prefix else key

        if key not in base_data:
            # New key - if it's a dict, report all its leaf paths instead of key
            if isinstance(value, dict):
                # For new nested objects, report all their leaf paths
                leaf_paths = _get_all_leaf_paths(value, current_path)
                modified_paths.update(leaf_paths)
            else:
                # For new non-dict values, report the path itself
                modified_paths.add(current_path)
        elif base_data[key] != value:
            # Value changed
            if isinstance(base_data[key], dict) and isinstance(value, dict):
                # Nested dict - check deeper for what specifically changed
                nested_paths = _get_modification_paths(
                    base_data[key], value, current_path
                )
                modified_paths.update(nested_paths)
            else:
                # Non-dict value changed
                modified_paths.add(current_path)

    # Check for deleted keys
    for key in base_data:
        if key not in context_data:
            current_path = f"{prefix}.{key}" if prefix else key
            modified_paths.add(current_path)

    return modified_paths


def _get_all_leaf_paths(data: dict, prefix: str = "") -> set:
    """Get all leaf paths in a nested dictionary."""
    leaf_paths = set()

    for key, value in data.items():
        current_path = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):
            # Recurse into nested dict
            nested_leafs = _get_all_leaf_paths(value, current_path)
            leaf_paths.update(nested_leafs)
        else:
            # This is a leaf
            leaf_paths.add(current_path)

    return leaf_paths


def _paths_conflict(path1: str, path2: str) -> bool:
    """Check if two dot-notation paths conflict with each other."""
    # Paths conflict if one is a prefix of the other or they are identical
    parts1 = path1.split(".")
    parts2 = path2.split(".")

    # Check if one path is a prefix of the other
    min_len = min(len(parts1), len(parts2))
    return parts1[:min_len] == parts2[:min_len]


def _deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries, with dict2 values taking precedence.

    None values in dict2 are treated as "no change" and will not overwrite
    existing values from dict1. This ensures parallel operations that set
    different variables in the same nested object preserve all changes.
    """
    result = dict1.copy()
    for key, value in dict2.items():
        if value is None:
            # None means "no change" - don't overwrite existing value
            continue
        elif (
            key in result and isinstance(result[key], dict) and isinstance(value, dict)
        ):
            result[key] = _deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


class ContextMerger:
    """Utilities for merging parallel context modifications."""

    @staticmethod
    def merge_contexts(contexts: List["GrimoireContext"]) -> "GrimoireContext":
        """Merge multiple contexts with simple merging (no conflict detection).

        This method merges the local data from multiple contexts into a single
        context. It assumes all contexts have the same parent and template resolver.
        It does NOT check for conflicts - use merge_contexts_with_base for that.

        Args:
            contexts: List of GrimoireContext instances to merge

        Returns:
            New GrimoireContext with merged data

        Raises:
            ContextMergeError: If contexts list is empty
        """
        if not contexts:
            raise ContextMergeError("Cannot merge empty context list")

        base_context = contexts[0]

        # Start with the first context's data
        try:
            merged_data = base_context._data
        except AttributeError as e:
            raise ContextMergeError("Invalid context object") from e

        # Merge data from all other contexts using deep merge
        merged_dict = dict(merged_data)

        for i, context in enumerate(contexts[1:], 1):
            try:
                context_data = context._data
            except AttributeError as e:
                raise ContextMergeError(f"Invalid context object at index {i}") from e

            # Use deep merge to handle nested structures intelligently
            context_dict = dict(context_data)
            merged_dict = _deep_merge_dicts(merged_dict, context_dict)

        # Convert back to PMap
        from pyrsistent import pmap

        merged_data = pmap(merged_dict)

        # Import here to avoid circular imports
        from .context import GrimoireContext

        return GrimoireContext(
            merged_data,
            base_context._parent,
            base_context._template_resolver,
            base_context._id,
        )

    @staticmethod
    def merge_contexts_with_strategy(
        contexts: List["GrimoireContext"], conflict_strategy: str = "error"
    ) -> "GrimoireContext":
        """Merge contexts with different conflict resolution strategies.

        Args:
            contexts: List of contexts to merge
            conflict_strategy: How to handle conflicts:
                - 'error': Raise error on conflicts (default)
                - 'last_wins': Later contexts override earlier ones
                - 'first_wins': Earlier contexts take precedence

        Returns:
            New GrimoireContext with merged data

        Raises:
            ContextMergeError: If invalid strategy or other merge issues
        """
        if not contexts:
            raise ContextMergeError("Cannot merge empty context list")

        if conflict_strategy not in ("error", "last_wins", "first_wins"):
            raise ContextMergeError(f"Invalid conflict strategy: {conflict_strategy}")

        logger.debug(
            f"Merging {len(contexts)} contexts with '{conflict_strategy}' "
            "conflict strategy"
        )

        base_context = contexts[0]
        merged_data = base_context._data

        for context in contexts[1:]:
            context_data = context._data

            if conflict_strategy == "error":
                # Check for conflicts and raise error
                conflicts = set(merged_data.keys()) & set(context_data.keys())
                if conflicts:
                    raise ContextMergeError(
                        f"Key conflicts in parallel merge: {conflicts}"
                    )

            # Merge data based on strategy
            for key, value in context_data.items():
                if key in merged_data:
                    if conflict_strategy == "first_wins":
                        # Skip - keep existing value
                        continue
                    elif conflict_strategy == "last_wins":
                        # Override with new value
                        pass

                merged_data = merged_data.set(key, value)

        # Import here to avoid circular imports
        from .context import GrimoireContext

        return GrimoireContext(
            merged_data,
            base_context._parent,
            base_context._template_resolver,
            base_context._id,
        )

    @staticmethod
    def merge_contexts_with_base(
        contexts: List["GrimoireContext"], base_context: "GrimoireContext"
    ) -> "GrimoireContext":
        """Merge multiple contexts with knowledge of the original base context.

        This method can detect what was actually modified by comparing to the base.

        Args:
            contexts: List of GrimoireContext instances to merge
            base_context: The original context that all operations started from

        Returns:
            New GrimoireContext with merged data

        Raises:
            ContextMergeError: If contexts list is empty or if key conflicts exist
        """
        if not contexts:
            raise ContextMergeError("Cannot merge empty context list")

        # Find what each context actually modified by comparing to base using paths
        modified_paths_per_context = []
        base_data = dict(base_context._data)

        for context in contexts:
            context_data = dict(context._data)
            modified_paths = _get_modification_paths(base_data, context_data)
            modified_paths_per_context.append(modified_paths)

        # Check for conflicts: paths that conflict with each other
        all_modified_paths: List[str] = []
        conflicted_paths = set()

        for modified_paths in modified_paths_per_context:
            for new_path in modified_paths:
                # Check if this path conflicts with any existing path
                for existing_path in all_modified_paths:
                    if _paths_conflict(new_path, existing_path):
                        conflicted_paths.add(new_path)
                        conflicted_paths.add(existing_path)
                all_modified_paths.append(new_path)

        if conflicted_paths:
            paths_str = sorted(conflicted_paths)
            # Example logging for conflict detection
            logger.warning(f"Path conflicts detected in parallel merge: {paths_str}")
            raise ContextMergeError(f"Path conflicts in parallel merge: {paths_str}")

        # Merge all contexts using the original merge logic (now safe from conflicts)
        return ContextMerger.merge_contexts(contexts)

    @staticmethod
    def execute_parallel_operations(
        base_context: "GrimoireContext",
        operations: List[Callable[["GrimoireContext"], "GrimoireContext"]],
    ) -> "GrimoireContext":
        """Execute operations in parallel and merge results.

        This method runs multiple context operations concurrently using a thread pool
        and then merges the results into a single context.

        Args:
            base_context: Starting context for all operations
            operations: List of functions that take and return GrimoireContext

        Returns:
            New GrimoireContext with merged results from all operations

        Raises:
            ContextMergeError: If operations fail or merging fails
        """
        if not operations:
            return base_context

        try:
            with ThreadPoolExecutor() as executor:
                # Submit all operations
                futures = [
                    executor.submit(operation, base_context) for operation in operations
                ]

                # Collect results as they complete
                results = []
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(
                            f"Parallel context operation failed: "
                            f"{type(e).__name__}: {e}"
                        )
                        raise ContextMergeError(
                            f"Parallel operation failed: {e}"
                        ) from e

                # Merge all results with base context knowledge
                result = ContextMerger.merge_contexts_with_base(results, base_context)
                logger.info(
                    f"Successfully executed {len(operations)} parallel operations "
                    "and merged results"
                )
                return result

        except Exception as e:
            if isinstance(e, ContextMergeError):
                raise
            raise ContextMergeError(f"Parallel execution failed: {e}") from e

    @staticmethod
    def execute_parallel_with_strategy(
        base_context: "GrimoireContext",
        operations: List[Callable[["GrimoireContext"], "GrimoireContext"]],
        conflict_strategy: str = "error",
    ) -> "GrimoireContext":
        """Execute operations in parallel with conflict resolution strategy.

        Args:
            base_context: Starting context for all operations
            operations: List of functions that take and return GrimoireContext
            conflict_strategy: How to handle merge conflicts

        Returns:
            New GrimoireContext with merged results

        Raises:
            ContextMergeError: If operations fail or merging fails
        """
        if not operations:
            return base_context

        try:
            with ThreadPoolExecutor() as executor:
                # Submit all operations
                futures = [
                    executor.submit(operation, base_context) for operation in operations
                ]

                # Collect results
                results = []
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        raise ContextMergeError(
                            f"Parallel operation failed: {e}"
                        ) from e

                # Merge with specified strategy
                return ContextMerger.merge_contexts_with_strategy(
                    results, conflict_strategy
                )

        except Exception as e:
            if isinstance(e, ContextMergeError):
                raise
            raise ContextMergeError(f"Parallel execution failed: {e}") from e
