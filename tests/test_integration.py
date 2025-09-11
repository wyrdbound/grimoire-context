"""Integration tests for GrimoireContext package."""

from typing import Any, Dict

import pytest

from grimoire_context import (
    ContextMergeError,
    GrimoireContext,
    InvalidContextOperation,
    TemplateError,
)


class JinjaLikeResolver:
    """Jinja2-like template resolver for integration testing."""

    def resolve_template(self, template_str: str, context_dict: Dict[str, Any]) -> Any:
        """Simple Jinja2-like template resolver."""
        import re

        # Handle simple variable substitution {{ var }}
        def replace_var(match):
            var_path = match.group(1).strip()
            return str(self._get_nested_value(context_dict, var_path))

        # Handle filters like {{ var | upper }}
        def replace_with_filter(match):
            var_path = match.group(1).strip()
            filter_name = match.group(2).strip()
            value = self._get_nested_value(context_dict, var_path)

            if filter_name == "upper":
                return str(value).upper()
            elif filter_name == "lower":
                return str(value).lower()
            elif filter_name == "title":
                return str(value).title()
            else:
                return str(value)

        # First try filters, then simple variables
        result = re.sub(
            r"\{\{\s*(\w+(?:\.\w+)*)\s*\|\s*(\w+)\s*\}\}",
            replace_with_filter,
            template_str,
        )
        result = re.sub(r"\{\{\s*(\w+(?:\.\w+)*)\s*\}\}", replace_var, result)

        return result

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get nested value using dot notation."""
        current = data
        for part in path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return f"MISSING:{path}"
        return current


class TestIntegrationScenarios:
    """Test realistic usage scenarios."""

    def test_rpg_character_management(self):
        """Test managing RPG character data."""
        # Global game context
        global_ctx = GrimoireContext(
            {"system": "knave_1e", "session_id": "session_001", "debug_mode": False}
        )

        # Character context
        character_ctx = global_ctx.create_child_context(
            {
                "character": {
                    "name": "Aragorn",
                    "level": 5,
                    "stats": {"hp": 45, "mp": 20},
                    "equipment": ["sword", "shield", "potion"],
                }
            }
        )

        # Combat encounter context
        combat_ctx = character_ctx.create_child_context(
            {
                "encounter": {"enemy": "Orc Warrior", "round": 1, "initiative": 15},
                "temp_buffs": {"strength_bonus": 2},
            }
        )

        # Test hierarchical access
        assert combat_ctx["system"] == "knave_1e"  # From global
        assert combat_ctx.get_variable("character.name") == "Aragorn"  # From character
        assert combat_ctx.get_variable("encounter.round") == 1  # From combat

        # Apply damage
        damaged_ctx = combat_ctx.set_variable("character.stats.hp", 35)

        # Use potion
        healed_ctx = damaged_ctx.set_variable("character.stats.hp", 45)
        used_potion_ctx = healed_ctx.set_variable(
            "character.equipment",
            ["sword", "shield"],  # Potion consumed
        )

        # Original contexts unchanged
        assert combat_ctx.get_variable("character.stats.hp") == 45
        assert len(combat_ctx.get_variable("character.equipment")) == 3

        # Final context has changes
        assert used_potion_ctx.get_variable("character.stats.hp") == 45
        assert len(used_potion_ctx.get_variable("character.equipment")) == 2

    def test_template_integration_workflow(self):
        """Test integration with template resolution."""
        resolver = JinjaLikeResolver()

        # Create context with template resolver
        context = GrimoireContext(
            {
                "character": {"name": "Frodo", "class": "rogue"},
                "dice": {"result": 18, "modifier": 3},
                "target": {"difficulty": 15},
            }
        ).set_template_resolver(resolver)

        # Test various template patterns
        greeting = context.resolve_template("Hello, {{ character.name }}!")
        assert greeting == "Hello, Frodo!"

        class_display = context.resolve_template(
            "{{ character.name }} the {{ character.class | title }}"
        )
        assert class_display == "Frodo the Rogue"

        roll_result = context.resolve_template(
            "Rolled {{ dice.result }} + {{ dice.modifier }} = "
            "{{ dice.result }}{{ dice.modifier }}"
        )
        assert "18" in roll_result and "3" in roll_result

        # Child context inherits resolver
        child_ctx = context.create_child_context({"scene": "tavern"})
        scene_desc = child_ctx.resolve_template(
            "{{ character.name }} enters the {{ scene }}"
        )
        assert scene_desc == "Frodo enters the tavern"

    def test_parallel_skill_checks(self):
        """Test parallel execution for multiple skill checks."""
        party_context = GrimoireContext(
            {
                "party": {
                    "aragorn": {"stealth": 12, "perception": 15},
                    "legolas": {"stealth": 18, "perception": 20},
                    "gimli": {"stealth": 8, "perception": 14},
                },
                "difficulty": 14,
            }
        )

        # Define skill check operations
        def aragorn_stealth_check(ctx):
            return ctx.set_variable("results.aragorn.stealth", "success")

        def legolas_stealth_check(ctx):
            return ctx.set_variable("results.legolas.stealth", "success")

        def gimli_stealth_check(ctx):
            return ctx.set_variable("results.gimli.stealth", "failure")

        # Execute all checks in parallel
        operations = [aragorn_stealth_check, legolas_stealth_check, gimli_stealth_check]
        result_ctx = party_context.execute_parallel(operations)

        # Check results
        assert result_ctx.get_variable("results.aragorn.stealth") == "success"
        assert result_ctx.get_variable("results.legolas.stealth") == "success"
        assert result_ctx.get_variable("results.gimli.stealth") == "failure"

        # Original party data preserved
        assert result_ctx.get_variable("party.aragorn.stealth") == 12

    def test_complex_nested_workflow(self):
        """Test complex nested operations and rollback scenarios."""
        # Start with base campaign context
        campaign = GrimoireContext(
            {
                "campaign": {"name": "Lord of the Rings", "chapter": 1},
                "world": {"time": "morning", "weather": "clear"},
            }
        )

        # Create scene context
        scene = campaign.create_child_context(
            {"location": "Rivendell", "npcs": ["Elrond", "Arwen"], "events": []}
        )

        # Simulate conversation sequence
        step1 = scene.set_variable("events", ["player_arrives"])
        step2 = step1.set_variable("events", ["player_arrives", "meets_elrond"])
        step3 = step2.set_variable("dialogue.elrond.mood", "welcoming")

        # Simulate different conversation branch (rollback scenario)
        alt_step2 = step1.set_variable("events", ["player_arrives", "meets_arwen"])
        alt_step3 = alt_step2.set_variable("dialogue.arwen.mood", "curious")

        # Both branches exist independently
        assert step3.get_variable("events") == ["player_arrives", "meets_elrond"]
        assert alt_step3.get_variable("events") == ["player_arrives", "meets_arwen"]

        # Both can access campaign data
        assert step3["campaign"]["name"] == "Lord of the Rings"
        assert alt_step3["campaign"]["name"] == "Lord of the Rings"

        # Original scene unchanged
        assert scene.get_variable("events") == []

    def test_error_handling_integration(self):
        """Test comprehensive error handling."""
        context = GrimoireContext({"valid": "data"})

        # Test template error without resolver
        with pytest.raises(TemplateError):
            context.resolve_template("{{ valid }}")

        # Test invalid context operations
        with pytest.raises(InvalidContextOperation):
            context["new_key"] = "value"  # Direct assignment forbidden

        # Test parallel execution errors
        def failing_operation(ctx):
            raise ValueError("Simulated failure")

        def working_operation(ctx):
            return ctx.set("result", "success")

        with pytest.raises(ContextMergeError):
            context.execute_parallel([failing_operation, working_operation])

    def test_large_scale_context_management(self):
        """Test performance and correctness with large contexts."""
        # Create large initial dataset
        large_data = {}
        for i in range(1000):
            large_data[f"item_{i}"] = {
                "id": i,
                "name": f"Item {i}",
                "properties": {
                    "value": i * 10,
                    "weight": i * 0.1,
                    "tags": [f"tag_{j}" for j in range(i % 5)],
                },
            }

        context = GrimoireContext(large_data)

        # Perform multiple operations
        updated = context.set_variable("item_500.properties.value", 9999)
        updated = updated.set("new_summary", "Large context test")
        updated = updated.discard("item_999")  # Remove last item

        # Verify operations
        assert updated.get_variable("item_500.properties.value") == 9999
        assert updated["new_summary"] == "Large context test"
        assert "item_999" not in updated

        # Original unchanged
        assert context.get_variable("item_500.properties.value") == 5000
        assert "new_summary" not in context
        assert "item_999" in context

        # Verify large structure integrity
        assert len(context) == 1000
        assert len(updated) == 1000  # 999 original + 1 new - 1 removed + 1 added

    def test_real_world_usage_patterns(self):
        """Test patterns that would be used in real Grimoire scenarios."""
        # Engine initialization
        engine_ctx = GrimoireContext(
            {
                "engine": {"version": "1.0", "debug": False},
                "grimoire": {"loaded_models": ["character", "spell", "item"]},
            }
        )

        # Flow execution context
        flow_ctx = engine_ctx.create_child_context(
            {"flow_id": "combat_resolution", "step_count": 0, "variables": {}}
        )

        # Step execution contexts
        step1_ctx = flow_ctx.create_child_context(
            {
                "step_name": "roll_initiative",
                "inputs": {"characters": ["player", "enemy"]},
                "outputs": {},
            }
        )

        # Execute step and capture outputs
        step1_result = step1_ctx.set_variable(
            "outputs.initiative_order", ["player", "enemy"]
        )
        step1_result = step1_result.set_variable("step_count", 1)

        # Next step gets results from previous
        step2_ctx = step1_result.create_child_context(
            {"step_name": "player_action", "inputs": {"action_type": "attack"}}
        )

        # Template integration for dynamic content
        resolver = JinjaLikeResolver()
        step2_with_templates = step2_ctx.set_template_resolver(resolver)

        action_desc = step2_with_templates.resolve_template(
            "{{ step_name }} step in {{ flow_id }} flow"
        )
        assert action_desc == "player_action step in combat_resolution flow"

        # Verify context hierarchy integrity
        assert step2_ctx["engine"]["version"] == "1.0"  # From engine
        assert step2_ctx["flow_id"] == "combat_resolution"  # From flow
        assert step2_ctx.get_variable("outputs.initiative_order") == [
            "player",
            "enemy",
        ]  # From step1
        assert step2_ctx["step_name"] == "player_action"  # From step2
