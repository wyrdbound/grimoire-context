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
