"""Tests for hierarchical context functionality."""

from grimoire_context import GrimoireContext


class TestHierarchicalContexts:
    """Test hierarchical context functionality."""

    def test_create_child_context(self):
        """Test creating child contexts."""
        parent = GrimoireContext({"global_var": "global_value"})
        child = parent.create_child_context({"local_var": "local_value"})

        assert child.parent is parent
        assert child["global_var"] == "global_value"  # From parent
        assert child["local_var"] == "local_value"  # From child

        # Parent doesn't see child data
        assert "local_var" not in parent

    def test_variable_shadowing(self):
        """Test that child variables shadow parent variables."""
        parent = GrimoireContext({"name": "parent_name", "unique": "parent_unique"})
        child = parent.create_child_context({"name": "child_name"})

        # Child shadows parent's 'name'
        assert child["name"] == "child_name"
        assert child["unique"] == "parent_unique"  # Not shadowed

        # Parent unchanged
        assert parent["name"] == "parent_name"

    def test_multi_level_hierarchy(self):
        """Test multiple levels of context hierarchy."""
        global_ctx = GrimoireContext({"system": "knave_1e", "debug": False})
        flow_ctx = global_ctx.create_child_context({"character_name": "Legolas"})
        step_ctx = flow_ctx.create_child_context({"current_roll": 15})

        # All levels accessible from step
        assert step_ctx["system"] == "knave_1e"  # From global
        assert step_ctx["character_name"] == "Legolas"  # From flow
        assert step_ctx["current_roll"] == 15  # From step

        # Flow can't see step data
        assert "current_roll" not in flow_ctx

        # Global can't see flow or step data
        assert "character_name" not in global_ctx
        assert "current_roll" not in global_ctx

    def test_child_context_with_initial_data(self):
        """Test creating child with initial data."""
        parent = GrimoireContext({"a": 1})
        child = parent.create_child_context({"b": 2, "c": 3})

        assert len(child) == 3
        assert child["a"] == 1
        assert child["b"] == 2
        assert child["c"] == 3

    def test_child_context_id(self):
        """Test child context ID handling."""
        parent = GrimoireContext(context_id="parent")
        child1 = parent.create_child_context()
        child2 = parent.create_child_context(context_id="custom-child")

        assert child1.context_id != parent.context_id
        assert child2.context_id == "custom-child"

    def test_template_resolver_inheritance(self):
        """Test that child contexts inherit template resolver."""
        from tests.test_context import MockTemplateResolver

        resolver = MockTemplateResolver()
        parent = GrimoireContext({"name": "Aragorn"}).set_template_resolver(resolver)
        child = parent.create_child_context({"title": "King"})

        # Child inherits resolver
        assert child.template_resolver is resolver

        # Child can use resolver
        result = child.resolve_template("{{ name }} the {{ title }}")
        assert result == "Aragorn the King"

    def test_immutable_operations_on_child(self):
        """Test immutable operations preserve hierarchy."""
        parent = GrimoireContext({"parent_var": "parent_value"})
        child = parent.create_child_context({"child_var": "child_value"})

        # Update child
        updated_child = child.set("new_var", "new_value")

        # Check hierarchy preserved
        assert updated_child.parent is parent
        assert updated_child["parent_var"] == "parent_value"
        assert updated_child["child_var"] == "child_value"
        assert updated_child["new_var"] == "new_value"

        # Original child unchanged
        assert "new_var" not in child

    def test_path_operations_in_hierarchy(self):
        """Test path operations work correctly in hierarchy."""
        parent = GrimoireContext({"config": {"system": "grimoire"}})
        child = parent.create_child_context({"character": {"name": "Frodo"}})

        # Can access parent paths
        assert child.get_variable("config.system") == "grimoire"

        # Can access child paths
        assert child.get_variable("character.name") == "Frodo"

        # Set new path in child
        updated = child.set_variable("character.hp", 50)
        assert updated.get_variable("character.hp") == 50

        # Parent unchanged
        assert not parent.has_variable("character")

    def test_deep_hierarchy_chain_view(self):
        """Test chain view works with deep hierarchies."""
        level1 = GrimoireContext({"l1": "value1"})
        level2 = level1.create_child_context({"l2": "value2"})
        level3 = level2.create_child_context({"l3": "value3"})
        level4 = level3.create_child_context({"l4": "value4"})

        # All levels accessible from deepest
        chain = level4.chain_view
        assert chain["l1"] == "value1"
        assert chain["l2"] == "value2"
        assert chain["l3"] == "value3"
        assert chain["l4"] == "value4"

        assert len(level4) == 4

    def test_variable_shadowing_with_paths(self):
        """Test variable shadowing with nested paths."""
        parent = GrimoireContext({"character": {"name": "Aragorn", "hp": 100}})
        child = parent.create_child_context({"character": {"name": "Legolas"}})

        # Child completely shadows parent's 'character'
        assert child.get_variable("character.name") == "Legolas"
        assert child.get_variable("character.hp") is None  # Not in child's character

        # Parent unchanged
        assert parent.get_variable("character.name") == "Aragorn"
        assert parent.get_variable("character.hp") == 100
