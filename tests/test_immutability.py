"""Tests for immutability guarantees."""

from grimoire_context import GrimoireContext


class TestImmutabilityGuarantees:
    """Test that contexts are truly immutable."""

    def test_original_data_unchanged_after_set(self):
        """Test that original context data is unchanged after set operations."""
        original_data = {"character": {"name": "Aragorn", "hp": 100}}
        context = GrimoireContext(original_data)

        # Modify context
        new_context = context.set("new_key", "new_value")

        # Original data and context unchanged
        assert "new_key" not in original_data
        assert "new_key" not in context
        assert "new_key" in new_context

        # Check that we get different instances
        assert context is not new_context

    def test_original_data_unchanged_after_path_set(self):
        """Test that original data unchanged after path operations."""
        original_data = {"character": {"name": "Aragorn", "hp": 100}}
        context = GrimoireContext(original_data)

        # Modify nested path
        new_context = context.set_variable("character.hp", 90)

        # Original data unchanged
        assert original_data["character"]["hp"] == 100
        assert context.get_variable("character.hp") == 100
        assert new_context.get_variable("character.hp") == 90

    def test_original_data_unchanged_after_update(self):
        """Test that update operations don't modify original."""
        original_data = {"a": 1, "b": 2}
        context = GrimoireContext(original_data)

        # Update context
        updates = {"b": 20, "c": 3}
        new_context = context.update(updates)

        # Original unchanged
        assert original_data == {"a": 1, "b": 2}
        assert context["b"] == 2
        assert "c" not in context

        # New context has changes
        assert new_context["b"] == 20
        assert new_context["c"] == 3

    def test_original_data_unchanged_after_discard(self):
        """Test that discard operations don't modify original."""
        original_data = {"a": 1, "b": 2, "c": 3}
        context = GrimoireContext(original_data)

        # Remove key
        new_context = context.discard("b")

        # Original unchanged
        assert "b" in original_data
        assert "b" in context

        # New context has removal
        assert "b" not in new_context
        assert new_context["a"] == 1
        assert new_context["c"] == 3

    def test_nested_data_immutability(self):
        """Test that nested data structures remain immutable."""
        nested_list = [1, 2, 3]
        nested_dict = {"inner": "value"}

        context = GrimoireContext({"list": nested_list, "dict": nested_dict})

        # Modify context with new nested data
        new_context = context.set_variable("list", [4, 5, 6])

        # Original nested structures unchanged
        assert nested_list == [1, 2, 3]
        assert context["list"] == [1, 2, 3]
        assert new_context["list"] == [4, 5, 6]

    def test_child_context_immutability(self):
        """Test that child contexts maintain immutability."""
        parent = GrimoireContext({"parent_var": "parent_value"})
        child = parent.create_child_context({"child_var": "child_value"})

        # Modify child
        new_child = child.set("new_var", "new_value")

        # Original parent and child unchanged
        assert "new_var" not in parent
        assert "new_var" not in child
        assert "new_var" in new_child

        # Parent reference preserved but parent itself unchanged
        assert new_child.parent is parent
        assert new_child.parent.local_data() == parent.local_data()

    def test_copy_creates_independent_contexts(self):
        """Test that copies are independent."""
        original = GrimoireContext({"shared": "value"})
        copy = original.copy()

        # Modify copy
        modified_copy = copy.set("new_key", "new_value")

        # Original unchanged
        assert "new_key" not in original
        assert "new_key" not in copy
        assert "new_key" in modified_copy

        # All have independent identities
        assert original.context_id != copy.context_id
        assert copy.context_id != modified_copy.context_id

    def test_template_resolver_immutability(self):
        """Test that template resolver changes are immutable."""
        from tests.test_context import MockTemplateResolver

        resolver1 = MockTemplateResolver()
        resolver2 = MockTemplateResolver()

        context = GrimoireContext({"var": "value"})
        context_with_resolver1 = context.set_template_resolver(resolver1)
        context_with_resolver2 = context_with_resolver1.set_template_resolver(resolver2)

        # Each context has its own resolver
        assert context.template_resolver is None
        assert context_with_resolver1.template_resolver is resolver1
        assert context_with_resolver2.template_resolver is resolver2

        # Original contexts unchanged
        assert context.template_resolver is None
        assert context_with_resolver1.template_resolver is resolver1

    def test_large_data_immutability(self):
        """Test immutability with larger data structures."""
        large_data = {
            f"key_{i}": {
                "nested": {"deep": f"value_{i}", "list": list(range(i, i + 10))}
            }
            for i in range(100)
        }

        context = GrimoireContext(large_data)

        # Make several modifications
        context1 = context.set("new_key", "new_value")
        context2 = context1.set_variable("key_50.nested.deep", "modified")
        context3 = context2.update({"additional": "data"})

        # Original unchanged
        assert "new_key" not in context
        assert context.get_variable("key_50.nested.deep") == "value_50"
        assert "additional" not in context

        # Each modification preserved
        assert context1["new_key"] == "new_value"
        assert context2.get_variable("key_50.nested.deep") == "modified"
        assert context3["additional"] == "data"

    def test_delete_variable_immutability(self):
        """Test that delete operations maintain immutability."""
        data = {
            "character": {
                "name": "Aragorn",
                "stats": {"hp": 100, "mp": 50},
                "equipment": ["sword", "shield"],
            }
        }
        context = GrimoireContext(data)

        # Delete nested variable
        context_after_delete = context.delete_variable("character.stats.hp")

        # Original unchanged
        assert context.has_variable("character.stats.hp")
        assert context.get_variable("character.stats.hp") == 100

        # New context has deletion
        assert not context_after_delete.has_variable("character.stats.hp")
        assert context_after_delete.has_variable(
            "character.stats.mp"
        )  # Other data preserved
        assert context_after_delete.has_variable(
            "character.name"
        )  # Other data preserved
