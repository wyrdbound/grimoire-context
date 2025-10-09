"""Tests for parallel execution functionality."""

import time

import pytest

from grimoire_context import ContextMergeError, GrimoireContext


def slow_operation_a(context: GrimoireContext) -> GrimoireContext:
    """Slow operation that sets result_a."""
    time.sleep(0.1)  # Simulate work
    return context.set("result_a", "value_a")


def slow_operation_b(context: GrimoireContext) -> GrimoireContext:
    """Slow operation that sets result_b."""
    time.sleep(0.1)  # Simulate work
    return context.set("result_b", "value_b")


def timing_operation_a(context: GrimoireContext) -> GrimoireContext:
    """Operation that records timing to test parallel execution."""
    time.sleep(0.05)  # Initial delay
    result_context = context.set("timing_a", time.time())
    time.sleep(0.1)  # Work simulation
    return result_context


def timing_operation_b(context: GrimoireContext) -> GrimoireContext:
    """Operation that records timing to test parallel execution."""
    time.sleep(0.05)  # Initial delay
    result_context = context.set("timing_b", time.time())
    time.sleep(0.1)  # Work simulation
    return result_context


def conflicting_operation(context: GrimoireContext) -> GrimoireContext:
    """Operation that conflicts with other operations."""
    return context.set("result_a", "conflicting_value")


class TestParallelExecution:
    """Test parallel execution functionality."""

    def test_execute_parallel_basic(self):
        """Test basic parallel execution without conflicts."""
        context = GrimoireContext({"base": "value"})

        operations = [slow_operation_a, slow_operation_b]
        result = context.execute_parallel(operations)

        # Results should be merged
        assert result["base"] == "value"  # Original data preserved
        assert result["result_a"] == "value_a"
        assert result["result_b"] == "value_b"

    def test_execute_parallel_timing(self):
        """Test that operations actually run in parallel by checking timing overlap."""
        context = GrimoireContext({"base": "value"})

        operations = [timing_operation_a, timing_operation_b]
        result = context.execute_parallel(operations)

        # If operations ran in parallel, their recorded times should overlap
        # (difference should be much less than the sleep duration)
        timing_a = result["timing_a"]
        timing_b = result["timing_b"]
        time_diff = abs(timing_a - timing_b)

        # If they ran sequentially, the difference would be ~0.15s (0.05 + 0.1)
        # If they ran in parallel, the difference should be much smaller
        assert time_diff < 0.1, (
            f"Operations appear to have run sequentially (time diff: {time_diff:.3f}s)"
        )

    def test_execute_parallel_with_conflicts(self):
        """Test parallel execution with conflicting operations."""
        context = GrimoireContext({"base": "value"})

        # Operations that set the same key
        operations = [slow_operation_a, conflicting_operation]

        with pytest.raises(ContextMergeError, match="conflicts"):
            context.execute_parallel(operations)

    def test_execute_parallel_empty_operations(self):
        """Test parallel execution with empty operations list."""
        context = GrimoireContext({"base": "value"})
        result = context.execute_parallel([])

        # Should return the original context
        assert result is context

    def test_execute_parallel_single_operation(self):
        """Test parallel execution with single operation."""
        context = GrimoireContext({"base": "value"})

        result = context.execute_parallel([slow_operation_a])

        assert result["base"] == "value"
        assert result["result_a"] == "value_a"

    def test_execute_parallel_with_path_operations(self):
        """Test parallel execution with path-based operations."""
        context = GrimoireContext({"character": {"name": "Aragorn"}})

        def set_hp(ctx):
            return ctx.set_variable("character.hp", 100)

        def set_mp(ctx):
            return ctx.set_variable("character.mp", 50)

        def set_level(ctx):
            return ctx.set_variable("stats.level", 5)

        operations = [set_hp, set_mp, set_level]
        result = context.execute_parallel(operations)

        assert result.get_variable("character.name") == "Aragorn"
        assert result.get_variable("character.hp") == 100
        assert result.get_variable("character.mp") == 50
        assert result.get_variable("stats.level") == 5

    def test_parallel_operation_isolation(self):
        """Test that parallel operations work on independent contexts."""
        context = GrimoireContext({"counter": 0})

        def increment_counter(ctx):
            current = ctx["counter"]
            time.sleep(0.1)  # Simulate race condition potential
            return ctx.set("counter", current + 1)

        # If operations weren't isolated, we might get race conditions
        # But since each operation gets the original context, results should be
        # predictable
        operations = [increment_counter, increment_counter]

        with pytest.raises(ContextMergeError, match="conflicts"):
            context.execute_parallel(operations)

    def test_parallel_with_hierarchical_contexts(self):
        """Test parallel execution with hierarchical contexts."""
        parent = GrimoireContext({"system": "grimoire"})
        child = parent.create_child_context({"character": "Frodo"})

        def set_hp(ctx):
            return ctx.set_variable("stats.hp", 100)

        def set_mp(ctx):
            return ctx.set_variable("stats.mp", 50)

        operations = [set_hp, set_mp]
        result = child.execute_parallel(operations)

        # Should preserve hierarchy
        assert result.parent is parent
        assert result["system"] == "grimoire"  # From parent
        assert result["character"] == "Frodo"  # From child
        assert result.get_variable("stats.hp") == 100
        assert result.get_variable("stats.mp") == 50

    def test_parallel_operation_error_handling(self):
        """Test error handling in parallel operations."""
        context = GrimoireContext({"base": "value"})

        def failing_operation(ctx):
            raise ValueError("Operation failed")

        def working_operation(ctx):
            return ctx.set("result", "success")

        operations = [failing_operation, working_operation]

        with pytest.raises(ContextMergeError, match="Parallel operation failed"):
            context.execute_parallel(operations)


class TestParallelNoneHandling:
    """Test None value handling in parallel execution."""

    def test_parallel_none_preservation_issue_reproduction(self):
        """Reproduce the exact bug from the issue."""
        ctx = GrimoireContext(
            {"variables": {"value1": None, "value2": None, "value3": None}}
        )

        def set_value1(context):
            return context.set_variable("variables.value1", 10)

        def set_value2(context):
            return context.set_variable("variables.value2", 20)

        def set_value3(context):
            return context.set_variable("variables.value3", 30)

        result = ctx.execute_parallel([set_value1, set_value2, set_value3])
        variables = result.get_variable("variables")

        # All values should be preserved, None values should not overwrite
        assert variables["value1"] == 10
        assert variables["value2"] == 20
        assert variables["value3"] == 30

    def test_parallel_mixed_none_and_values(self):
        """Test parallel operations with mix of None and real values."""
        ctx = GrimoireContext({"data": {"a": 1, "b": None, "c": 3, "d": None}})

        def set_b(context):
            return context.set_variable("data.b", 2)

        def set_d(context):
            return context.set_variable("data.d", 4)

        result = ctx.execute_parallel([set_b, set_d])
        data = result.get_variable("data")

        assert data["a"] == 1  # Original value preserved
        assert data["b"] == 2  # None overwritten with value
        assert data["c"] == 3  # Original value preserved
        assert data["d"] == 4  # None overwritten with value

    def test_deep_merge_none_skipping(self):
        """Test that parallel execution skips None values during merge."""
        # Start with a context that has None values in nested structure
        ctx = GrimoireContext(
            {"data": {"a": None, "b": None, "c": {"x": None, "y": None}}}
        )

        def set_a_and_cx(context):
            # Sets data.a to 1 and data.c.x to 10
            updated = context.set_variable("data.a", 1)
            return updated.set_variable("data.c.x", 10)

        def set_b_and_cy(context):
            # Sets data.b to 2 and data.c.y to 20
            updated = context.set_variable("data.b", 2)
            return updated.set_variable("data.c.y", 20)

        result = ctx.execute_parallel([set_a_and_cx, set_b_and_cy])

        # All values should be preserved - None values don't overwrite
        assert result.get_variable("data.a") == 1  # Set by first operation
        assert result.get_variable("data.b") == 2  # Set by second operation
        assert result.get_variable("data.c.x") == 10  # Set by first operation
        assert result.get_variable("data.c.y") == 20  # Set by second operation

    def test_parallel_none_in_new_nested_objects(self):
        """Test parallel operations creating new nested objects with None values."""
        ctx = GrimoireContext({})

        def add_stats(context):
            return context.set_variable("stats", {"hp": 100, "mp": None})

        def add_info(context):
            return context.set_variable("info", {"name": "Test", "level": None})

        result = ctx.execute_parallel([add_stats, add_info])

        assert result.get_variable("stats.hp") == 100
        assert result.get_variable("stats.mp") is None  # None is allowed in new data
        assert result.get_variable("info.name") == "Test"
        assert result.get_variable("info.level") is None

    def test_parallel_empty_dict_values(self):
        """Test that empty dicts are treated differently from None."""
        ctx = GrimoireContext({"data": {"a": 1, "b": 2}})

        def set_empty_dict(context):
            return context.set_variable("data.c", {})

        def set_value(context):
            return context.set_variable("data.d", 4)

        result = ctx.execute_parallel([set_empty_dict, set_value])

        assert result.get_variable("data.a") == 1
        assert result.get_variable("data.b") == 2
        assert result.get_variable("data.c") == {}
        assert result.get_variable("data.d") == 4


class TestContextMerger:
    """Test ContextMerger class directly."""

    def test_merge_contexts_basic(self):
        """Test basic context merging."""
        from grimoire_context.merge import ContextMerger

        base = GrimoireContext({"a": 1})
        context1 = base.set("b", 2)
        context2 = base.set("c", 3)

        merged = ContextMerger.merge_contexts([context1, context2])

        assert merged["a"] == 1  # From base (both contexts have it)
        assert merged["b"] == 2  # From context1
        assert merged["c"] == 3  # From context2

    def test_merge_contexts_with_conflicts(self):
        """Test context merging with conflicts."""
        from grimoire_context.merge import ContextMerger

        base = GrimoireContext({"a": 1})
        context1 = base.set("b", 2)
        context2 = base.set("b", 3)  # Conflict on 'b'

        with pytest.raises(ContextMergeError, match="conflicts"):
            ContextMerger.merge_contexts_with_base([context1, context2], base)

    def test_merge_contexts_empty_list(self):
        """Test merging empty context list."""
        from grimoire_context.merge import ContextMerger

        with pytest.raises(ContextMergeError, match="Cannot merge empty context list"):
            ContextMerger.merge_contexts([])

    def test_merge_with_strategy_last_wins(self):
        """Test merging with last-wins strategy."""
        from grimoire_context.merge import ContextMerger

        base = GrimoireContext({"a": 1})
        context1 = base.set("b", 2)
        context2 = base.set("b", 3)  # Should win

        merged = ContextMerger.merge_contexts_with_strategy(
            [context1, context2], conflict_strategy="last_wins"
        )

        assert merged["b"] == 3  # Last value wins

    def test_merge_with_strategy_first_wins(self):
        """Test merging with first-wins strategy."""
        from grimoire_context.merge import ContextMerger

        base = GrimoireContext({"a": 1})
        context1 = base.set("b", 2)  # Should win
        context2 = base.set("b", 3)

        merged = ContextMerger.merge_contexts_with_strategy(
            [context1, context2], conflict_strategy="first_wins"
        )

        assert merged["b"] == 2  # First value wins

    def test_execute_parallel_with_strategy(self):
        """Test parallel execution with conflict strategy."""
        from grimoire_context.merge import ContextMerger

        context = GrimoireContext({"base": "value"})

        def set_result_1(ctx):
            return ctx.set("result", "first")

        def set_result_2(ctx):
            return ctx.set("result", "second")

        operations = [set_result_1, set_result_2]

        # Should succeed with strategy
        result = ContextMerger.execute_parallel_with_strategy(
            context, operations, "last_wins"
        )

        assert result["base"] == "value"
        assert result["result"] in ["first", "second"]  # One of them should win
