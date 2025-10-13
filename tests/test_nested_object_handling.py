"""Tests for nested path setting on non-dict objects."""

from grimoire_context import GrimoireContext


class SimpleObject:
    """A simple test object with attributes."""

    def __init__(self):
        self.name = "Test Name"
        self.value = 42
        self.items = []

    def __eq__(self, other):
        if not isinstance(other, SimpleObject):
            return False
        return (
            self.name == other.name
            and self.value == other.value
            and self.items == other.items
        )

    def __repr__(self):
        return f"SimpleObject(name={self.name}, value={self.value}, items={self.items})"


class NestedObject:
    """A nested test object with object attributes."""

    def __init__(self):
        self.outer_name = "Outer"
        self.inner = SimpleObject()

    def __repr__(self):
        return f"NestedObject(outer_name={self.outer_name}, inner={self.inner})"


class DictLikeObject:
    """An object that supports both attribute and item access."""

    def __init__(self):
        self._data = {"key1": "value1", "key2": "value2"}

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __repr__(self):
        return f"DictLikeObject({self._data})"


class TestNestedObjectHandling:
    """Test nested path setting on non-dict objects."""

    def test_set_nested_path_on_simple_object(self):
        """Test setting a nested path on a simple object."""
        context = GrimoireContext()
        obj = SimpleObject()

        # Store the object
        context = context.set_variable("character", obj)
        assert context.get_variable("character.name") == "Test Name"
        assert context.get_variable("character.value") == 42

        # Set a nested path on the object
        updated = context.set_variable("character.name", "New Name")

        # Object should be preserved with updated attribute
        result = updated.get_variable("character")
        assert isinstance(result, SimpleObject)
        assert result.name == "New Name"
        assert result.value == 42  # Other attributes preserved
        assert result.items == []  # Other attributes preserved

        # Original context unchanged
        orig_obj = context.get_variable("character")
        assert orig_obj.name == "Test Name"

    def test_set_nested_path_on_object_list_attribute(self):
        """Test setting a list attribute on an object."""
        context = GrimoireContext()
        obj = SimpleObject()

        context = context.set_variable("outputs.character", obj)
        updated = context.set_variable("outputs.character.items", ["sword", "shield"])

        result = updated.get_variable("outputs.character")
        assert isinstance(result, SimpleObject)
        assert result.items == ["sword", "shield"]
        assert result.name == "Test Name"  # Other attributes preserved
        assert result.value == 42

    def test_set_deeply_nested_path_on_object(self):
        """Test setting a deeply nested path on nested objects."""
        context = GrimoireContext()
        obj = NestedObject()

        # Store nested object
        context = context.set_variable("data", obj)

        # Set a path on the inner object
        updated = context.set_variable("data.inner.name", "Updated Inner Name")

        result = updated.get_variable("data")
        assert isinstance(result, NestedObject)
        assert result.outer_name == "Outer"
        assert isinstance(result.inner, SimpleObject)
        assert result.inner.name == "Updated Inner Name"
        assert result.inner.value == 42  # Other inner attributes preserved

    def test_set_nested_path_on_dict_like_object(self):
        """Test setting nested path on object with __setitem__."""
        context = GrimoireContext()
        obj = DictLikeObject()

        context = context.set_variable("config", obj)
        updated = context.set_variable("config.key1", "new_value")

        result = updated.get_variable("config")
        # Should preserve object type
        assert isinstance(result, DictLikeObject)
        assert result["key1"] == "new_value"
        assert result["key2"] == "value2"  # Other items preserved

    def test_object_immutability_preserved(self):
        """Test that object modifications maintain immutability."""
        context = GrimoireContext()
        original_obj = SimpleObject()
        original_obj.name = "Original"

        context = context.set_variable("obj", original_obj)
        updated = context.set_variable("obj.name", "Modified")

        # Original object should be unchanged
        assert original_obj.name == "Original"

        # Context should have a copy with the change
        result = updated.get_variable("obj")
        assert result.name == "Modified"
        assert result is not original_obj

    def test_multiple_nested_updates_on_object(self):
        """Test multiple nested updates on the same object."""
        context = GrimoireContext()
        obj = SimpleObject()

        context = context.set_variable("character", obj)
        context = context.set_variable("character.name", "Hero")
        context = context.set_variable("character.value", 100)
        context = context.set_variable("character.items", ["potion"])

        result = context.get_variable("character")
        assert isinstance(result, SimpleObject)
        assert result.name == "Hero"
        assert result.value == 100
        assert result.items == ["potion"]

    def test_nested_path_with_new_attribute(self):
        """Test setting a new attribute on an object via nested path."""
        context = GrimoireContext()
        obj = SimpleObject()

        context = context.set_variable("character", obj)
        # Set a new attribute that doesn't exist on the original object
        updated = context.set_variable("character.new_attr", "new_value")

        result = updated.get_variable("character")
        assert isinstance(result, SimpleObject)
        assert hasattr(result, "new_attr")
        assert result.new_attr == "new_value"
        # Original attributes still present
        assert result.name == "Test Name"

    def test_mixed_dict_and_object_nesting(self):
        """Test nested paths with mixed dict and object types."""
        context = GrimoireContext()

        # Create structure: dict -> object -> dict
        obj = SimpleObject()
        context = context.set_variable("level1.character", obj)
        context = context.set_variable("level1.character.name", "Mixed Test")

        # Verify structure
        level1 = context.get_variable("level1")
        assert isinstance(level1, dict)
        assert isinstance(level1["character"], SimpleObject)
        assert level1["character"].name == "Mixed Test"

    def test_object_to_dict_fallback_warning(self):
        """Test that objects without setattr/setitem get converted to dict."""

        class ImmutableObject:
            """Object that doesn't support attribute assignment."""

            __slots__ = ("value",)

            def __init__(self):
                object.__setattr__(self, "value", 42)

            def __setattr__(self, name, value):
                raise AttributeError("Cannot set attribute")

        context = GrimoireContext()
        obj = ImmutableObject()

        # This should fall back to dict conversion
        context = context.set_variable("obj", obj)
        updated = context.set_variable("obj.new_key", "new_value")

        # Should be converted to dict
        result = updated.get_variable("obj")
        assert isinstance(result, dict)
        assert result["new_key"] == "new_value"

    def test_real_world_scenario_from_issue(self):
        """Test the exact scenario from the issue description."""

        class TestObject:
            def __init__(self):
                self.name = "Original Name"
                self.inventory = []
                self.level = 5

        context = GrimoireContext()
        test_obj = TestObject()

        # Step 1: Store the object
        context = context.set_variable("outputs.character", test_obj)
        stored = context.get_variable("outputs.character")
        assert isinstance(stored, TestObject)
        assert stored.name == "Original Name"

        # Step 2: Set nested path (this should NOT break the object)
        context = context.set_variable("outputs.character.inventory", ["new_item"])
        result = context.get_variable("outputs.character")

        # Verify object is preserved
        assert isinstance(result, TestObject)
        assert result.name == "Original Name"
        assert result.inventory == ["new_item"]
        assert result.level == 5


class TestBackwardCompatibility:
    """Test that existing dict-based functionality still works."""

    def test_dict_nested_path_setting(self):
        """Test that dict-based nested path setting still works."""
        context = GrimoireContext()
        context = context.set_variable("character.stats.hp", 100)

        assert context.get_variable("character.stats.hp") == 100
        assert isinstance(context.get_variable("character"), dict)
        assert isinstance(context.get_variable("character.stats"), dict)

    def test_mixed_dict_and_object_paths(self):
        """Test that we can have both dicts and objects in paths."""
        context = GrimoireContext()
        obj = SimpleObject()

        # Set object in dict
        context = context.set_variable("data.obj", obj)
        # Set dict nested in object
        context = context.set_variable("data.obj.name", "Updated")

        data = context.get_variable("data")
        assert isinstance(data, dict)
        assert isinstance(data["obj"], SimpleObject)
        assert data["obj"].name == "Updated"

    def test_create_new_nested_dicts(self):
        """Test creating new nested dict structures from scratch."""
        context = GrimoireContext()
        context = context.set_variable("a.b.c.d", "deep_value")

        assert context.get_variable("a.b.c.d") == "deep_value"
        assert isinstance(context.get_variable("a"), dict)
        assert isinstance(context.get_variable("a.b"), dict)
        assert isinstance(context.get_variable("a.b.c"), dict)
