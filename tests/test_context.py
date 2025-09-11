"""Tests for the main GrimoireContext class."""

from typing import Any, Dict

import pytest

from grimoire_context import GrimoireContext, InvalidContextOperation, TemplateError


class MockTemplateResolver:
    """Mock template resolver for testing."""

    def resolve_template(self, template_str: str, context_dict: Dict[str, Any]) -> Any:
        """Simple template resolver that replaces {{ var }} with context values."""
        import re

        def replace_var(match):
            var_name = match.group(1).strip()
            return str(context_dict.get(var_name, f"MISSING:{var_name}"))

        return re.sub(r"\{\{\s*(\w+)\s*\}\}", replace_var, template_str)


class TestGrimoireContextBasics:
    """Test basic context functionality."""

    def test_empty_context_creation(self):
        """Test creating an empty context."""
        context = GrimoireContext()
        assert len(context) == 0
        assert not context
        assert dict(context) == {}

    def test_context_with_initial_data(self):
        """Test creating context with initial data."""
        data = {"name": "Aragorn", "hp": 45}
        context = GrimoireContext(data)
        assert len(context) == 2
        assert context["name"] == "Aragorn"
        assert context["hp"] == 45
        assert dict(context) == data

    def test_context_id_generation(self):
        """Test that contexts get unique IDs."""
        context1 = GrimoireContext()
        context2 = GrimoireContext()
        assert context1.context_id != context2.context_id

    def test_custom_context_id(self):
        """Test setting custom context ID."""
        context = GrimoireContext(context_id="test-id")
        assert context.context_id == "test-id"


class TestDictInterface:
    """Test dict-like interface."""

    def test_getitem(self):
        """Test __getitem__ access."""
        context = GrimoireContext({"key": "value"})
        assert context["key"] == "value"

    def test_getitem_keyerror(self):
        """Test KeyError on missing key."""
        context = GrimoireContext()
        with pytest.raises(KeyError):
            _ = context["missing"]

    def test_setitem_forbidden(self):
        """Test that direct assignment is forbidden."""
        context = GrimoireContext()
        with pytest.raises(InvalidContextOperation):
            context["key"] = "value"

    def test_contains(self):
        """Test __contains__ operator."""
        context = GrimoireContext({"key": "value"})
        assert "key" in context
        assert "missing" not in context

    def test_get_with_default(self):
        """Test get() method with default."""
        context = GrimoireContext({"key": "value"})
        assert context.get("key") == "value"
        assert context.get("missing") is None
        assert context.get("missing", "default") == "default"

    def test_keys_values_items(self):
        """Test keys(), values(), and items() methods."""
        data = {"a": 1, "b": 2}
        context = GrimoireContext(data)

        assert set(context.keys()) == {"a", "b"}
        assert set(context.values()) == {1, 2}
        assert set(context.items()) == {("a", 1), ("b", 2)}

    def test_iteration(self):
        """Test iterating over context."""
        data = {"a": 1, "b": 2, "c": 3, "d": 4}
        context = GrimoireContext(data)
        assert set(context) == {"a", "b", "c", "d"}

    def test_bool_conversion(self):
        """Test boolean conversion."""
        empty_context = GrimoireContext()
        non_empty_context = GrimoireContext({"key": "value"})

        assert not empty_context
        assert non_empty_context

    def test_equality(self):
        """Test context equality."""
        context1 = GrimoireContext({"a": 1, "b": 2})
        context2 = GrimoireContext({"a": 1, "b": 2})
        context3 = GrimoireContext({"a": 1, "b": 3})

        assert context1 == context2
        assert context1 != context3

    def test_deep_equality(self):
        """Test context equality."""
        context1 = GrimoireContext({"a": 1, "b": {"1": 1, "2": 2}})
        context2 = GrimoireContext({"a": 1, "b": {"1": 1, "2": 2}})
        context3 = GrimoireContext({"a": 1, "b": {"1": 1, "2": 3}})

        assert context1 == context2
        assert context1 != context3


class TestImmutableOperations:
    """Test immutable operations."""

    def test_set_operation(self):
        """Test immutable set operation."""
        original = GrimoireContext({"a": 1})
        updated = original.set("b", 2)

        # Original unchanged
        assert "b" not in original
        assert len(original) == 1

        # New context has update
        assert updated["b"] == 2
        assert len(updated) == 2
        assert updated["a"] == 1  # Original data preserved

    def test_discard_operation(self):
        """Test immutable discard operation."""
        original = GrimoireContext({"a": 1, "b": 2})
        updated = original.discard("b")

        # Original unchanged
        assert "b" in original
        assert len(original) == 2

        # New context has removal
        assert "b" not in updated
        assert len(updated) == 1
        assert updated["a"] == 1  # Other data preserved

    def test_update_operation(self):
        """Test immutable update operation."""
        original = GrimoireContext({"a": 1})
        updates = {"b": 2, "c": 3}
        updated = original.update(updates)

        # Original unchanged
        assert len(original) == 1

        # New context has updates
        assert len(updated) == 3
        assert updated["a"] == 1
        assert updated["b"] == 2
        assert updated["c"] == 3

    def test_copy_operation(self):
        """Test context copying."""
        original = GrimoireContext({"a": 1}, context_id="original")
        copy = original.copy()
        copy_with_id = original.copy("new-id")

        # Same data, different IDs
        assert copy.to_dict() == original.to_dict()
        assert copy.context_id != original.context_id
        assert copy_with_id.context_id == "new-id"


class TestPathOperations:
    """Test dot notation path operations."""

    def test_set_simple_path(self):
        """Test setting simple path."""
        context = GrimoireContext()
        updated = context.set_variable("name", "Aragorn")
        assert updated.get_variable("name") == "Aragorn"

    def test_set_nested_path(self):
        """Test setting nested path."""
        context = GrimoireContext()
        updated = context.set_variable("character.stats.hp", 100)

        assert updated.get_variable("character.stats.hp") == 100
        assert updated.get_variable("character.stats") == {"hp": 100}

    def test_get_nested_path_with_default(self):
        """Test getting nested path with default."""
        context = GrimoireContext({"character": {"name": "Aragorn"}})

        assert context.get_variable("character.name") == "Aragorn"
        assert context.get_variable("character.missing") is None
        assert context.get_variable("character.missing", "default") == "default"

    def test_has_variable(self):
        """Test checking if variable exists."""
        context = GrimoireContext({"character": {"name": "Aragorn"}})

        assert context.has_variable("character")
        assert context.has_variable("character.name")
        assert not context.has_variable("character.missing")
        assert not context.has_variable("missing")

    def test_delete_variable(self):
        """Test deleting variables."""
        data = {"character": {"name": "Aragorn", "hp": 100}}
        context = GrimoireContext(data)

        # Delete nested variable
        updated = context.delete_variable("character.hp")
        assert not updated.has_variable("character.hp")
        assert updated.has_variable("character.name")

        # Delete top-level variable
        updated2 = updated.delete_variable("character")
        assert not updated2.has_variable("character")


class TestTemplateResolver:
    """Test template resolution functionality."""

    def test_no_resolver_error(self):
        """Test error when no resolver is configured."""
        context = GrimoireContext({"name": "Aragorn"})
        with pytest.raises(TemplateError, match="No template resolver configured"):
            context.resolve_template("{{ name }}")

    def test_set_template_resolver(self):
        """Test setting template resolver."""
        context = GrimoireContext({"name": "Aragorn"})
        resolver = MockTemplateResolver()

        context_with_resolver = context.set_template_resolver(resolver)
        assert context_with_resolver.template_resolver is resolver
        assert context.template_resolver is None  # Original unchanged

    def test_template_resolution(self):
        """Test basic template resolution."""
        context = GrimoireContext({"name": "Aragorn", "level": 5})
        resolver = MockTemplateResolver()
        context_with_resolver = context.set_template_resolver(resolver)

        result = context_with_resolver.resolve_template("Hello {{ name }}")
        assert result == "Hello Aragorn"

    def test_template_resolution_with_missing_var(self):
        """Test template resolution with missing variable."""
        context = GrimoireContext({"name": "Aragorn"})
        resolver = MockTemplateResolver()
        context_with_resolver = context.set_template_resolver(resolver)

        result = context_with_resolver.resolve_template("{{ missing }}")
        assert result == "MISSING:missing"


class TestUtilityMethods:
    """Test utility methods."""

    def test_to_dict(self):
        """Test converting to dictionary."""
        data = {"a": 1, "b": {"c": 2}}
        context = GrimoireContext(data)
        assert context.to_dict() == data

    def test_local_data(self):
        """Test getting local data only."""
        parent_data = {"a": 1}
        data = {"b": 2, "c": 3}
        context = GrimoireContext(data, parent=GrimoireContext(parent_data))

        # Local data should only include 'b' and 'c'
        assert context.local_data() == data

    def test_repr(self):
        """Test string representation."""
        context = GrimoireContext({"a": 1}, context_id="test")
        repr_str = repr(context)
        assert "GrimoireContext" in repr_str
        assert "test" in repr_str
        assert "{'a': 1}" in repr_str
