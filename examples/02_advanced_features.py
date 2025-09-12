#!/usr/bin/env python3
"""
Advanced GrimoireContext Features

This example demonstrates advanced features of grimoire-context:
- Template resolution with custom resolvers
- Complex hierarchical structures
- Parallel execution capabilities
- Error handling patterns
- Real-world usage scenarios
"""

from grimoire_context import GrimoireContext, ContextMergeError
from grimoire_context.protocols import TemplateResolver
from typing import Any, Dict


class SimpleTemplateResolver:
    """Simple template resolver using basic string substitution."""
    
    def resolve_template(self, template_str: str, context_dict: Dict[str, Any]) -> str:
        """Resolve template using simple {variable} substitution."""
        try:
            return template_str.format(**context_dict)
        except KeyError as e:
            from grimoire_context.exceptions import TemplateError
            raise TemplateError(f"Template variable not found: {e}")


def example_template_resolution():
    """Demonstrate template resolution functionality."""
    print("=== Template Resolution ===")
    
    # Create context with template resolver
    resolver = SimpleTemplateResolver()
    context = GrimoireContext({
        "player_name": "Diana",
        "class": "paladin",
        "level": 8,
        "location": "Crystal Caves"
    }, template_resolver=resolver)
    
    # Resolve simple templates
    greeting = context.resolve_template("Welcome, {player_name} the {class}!")
    print(f"Greeting: {greeting}")
    
    status = context.resolve_template("Level {level} {class} in {location}")
    print(f"Status: {status}")
    
    # Template resolution in child contexts
    combat_context = context.create_child_context({
        "enemy": "Crystal Golem",
        "enemy_hp": 45
    })
    
    combat_msg = combat_context.resolve_template(
        "{player_name} battles {enemy} (HP: {enemy_hp}) in {location}!"
    )
    print(f"Combat: {combat_msg}")
    
    # Handle template errors
    try:
        invalid = context.resolve_template("Invalid {missing_variable} template")
    except Exception as e:
        print(f"Template error (expected): {e}")


def example_complex_hierarchy():
    """Demonstrate complex hierarchical context structures."""
    print("\n=== Complex Hierarchical Structures ===")
    
    # Game world context
    world_context = GrimoireContext({
        "world_name": "Aethermoor",
        "season": "winter",
        "global_modifiers": {
            "temperature": -10,
            "visibility": 0.7
        },
        "rules": {
            "magic_level": "high",
            "technology_level": "medieval"
        }
    })
    
    # Region-specific context
    region_context = world_context.create_child_context({
        "region_name": "Frostwind Mountains",
        "local_weather": "blizzard",
        "global_modifiers": {  # This will override world modifiers
            "temperature": -25,
            "visibility": 0.3,
            "wind_speed": 40
        }
    })
    
    # Settlement context within region
    settlement_context = region_context.create_child_context({
        "settlement_name": "Ironhold",
        "population": 1200,
        "defenses": {
            "walls": "stone",
            "guards": 50,
            "magical_wards": True
        }
    })
    
    # Individual building context
    tavern_context = settlement_context.create_child_context({
        "building_type": "tavern",
        "name": "The Frozen Mug",
        "patrons": 15,
        "warmth_bonus": 20  # Overrides cold temperature inside
    })
    
    print("Context hierarchy demonstration:")
    print(f"World: {world_context['world_name']} ({world_context['season']})")
    print(f"Region: {region_context['region_name']}")
    print(f"  Temperature: {region_context.get_variable('global_modifiers.temperature')}°")
    print(f"Settlement: {settlement_context['settlement_name']} (pop: {settlement_context['population']})")
    print(f"Tavern: {tavern_context['name']} (patrons: {tavern_context['patrons']})")
    print(f"  Magic level (inherited): {tavern_context.get_variable('rules.magic_level')}")
    print(f"  Local weather (inherited): {tavern_context['local_weather']}")


def example_parallel_execution():
    """Demonstrate parallel execution with conflict handling."""
    print("\n=== Parallel Execution ===")
    
    # Base character context
    character = GrimoireContext({
        "name": "Erik",
        "hp": 100,
        "mp": 75,
        "inventory": {
            "gold": 250,
            "items": ["sword", "potion", "map"]
        },
        "stats": {"str": 16, "dex": 14, "int": 12}
    })
    
    print(f"Starting character: HP={character['hp']}, MP={character['mp']}, Gold={character.get_variable('inventory.gold')}")
    
    # Define parallel operations (non-conflicting)
    safe_operations = [
        lambda ctx: ctx.set_variable("hp", ctx["hp"] - 15),  # Take damage
        lambda ctx: ctx.set_variable("mp", ctx["mp"] - 10),  # Use mana
        lambda ctx: ctx.set_variable("experience", ctx.get("experience", 0) + 100),  # Gain XP
        lambda ctx: ctx.set_variable("location", "combat_zone")  # Update location
    ]
    
    try:
        result = character.execute_parallel(safe_operations)
        print("Parallel operations succeeded:")
        print(f"  HP: {result['hp']} (was {character['hp']})")
        print(f"  MP: {result['mp']} (was {character['mp']})")
        print(f"  XP: {result['experience']}")
        print(f"  Location: {result['location']}")
        
    except ContextMergeError as e:
        print(f"Merge conflict: {e}")
    
    # Demonstrate conflict detection
    print("\nTesting conflict detection:")
    conflicting_operations = [
        lambda ctx: ctx.set_variable("hp", 50),   # Operation 1 sets HP to 50
        lambda ctx: ctx.set_variable("hp", 75),   # Operation 2 sets HP to 75 - CONFLICT!
        lambda ctx: ctx.set_variable("mp", 30),   # Operation 3 sets MP (no conflict)
    ]
    
    try:
        conflict_result = character.execute_parallel(conflicting_operations)
        print("No conflict detected (unexpected)")
    except ContextMergeError as e:
        print(f"Conflict detected (expected): {e}")


def example_real_world_rpg_scenario():
    """Demonstrate a real-world RPG scenario."""
    print("\n=== Real-World RPG Scenario ===")
    
    # Campaign context
    campaign = GrimoireContext({
        "campaign_name": "The Shadow War",
        "session_number": 12,
        "party_level": 6,
        "world_state": {
            "war_progress": 0.6,
            "major_npcs_alive": ["King Aldric", "Mage Lyrina", "General Voss"],
            "artifacts_found": 2
        }
    })
    
    # Party context
    party = campaign.create_child_context({
        "party_size": 4,
        "shared_resources": {
            "gold": 1500,
            "rations": 12,
            "rope_feet": 150
        },
        "current_quest": "Retrieve the Crystal of Storms"
    })
    
    # Individual character context
    wizard = party.create_child_context({
        "character_name": "Zara the Wise", 
        "class": "wizard",
        "level": 6,
        "hp": 38,
        "max_hp": 42,
        "spell_slots": {1: 2, 2: 3, 3: 2},
        "prepared_spells": ["Magic Missile", "Shield", "Fireball", "Counterspell"],
        "equipment": {
            "weapon": "Staff of Power",
            "armor": "Robes of Protection",
            "misc": ["Spellbook", "Component Pouch", "Healing Potion"]
        }
    })
    
    print("RPG Session Context:")
    print(f"Campaign: {campaign['campaign_name']} (Session {campaign['session_number']})")
    print(f"Quest: {wizard['current_quest']}")
    print(f"Character: {wizard['character_name']} (Level {wizard['level']} {wizard['class']})")
    print(f"Health: {wizard['hp']}/{wizard['max_hp']}")
    print(f"Party gold: {wizard.get_variable('shared_resources.gold')}")
    print(f"War progress: {wizard.get_variable('world_state.war_progress') * 100:.0f}%")
    
    # Simulate combat round - parallel spell effects
    print("\nCombat round simulation:")
    combat_operations = [
        # Cast fireball (uses 3rd level slot)
        lambda ctx: ctx.set_variable("spell_slots.3", ctx.get_variable("spell_slots.3", 0) - 1),
        # Take some damage
        lambda ctx: ctx.set_variable("hp", max(0, ctx["hp"] - 8)),
        # Use healing potion
        lambda ctx: ctx.set_variable("equipment.misc", 
                                   [item for item in ctx.get_variable("equipment.misc", []) 
                                    if item != "Healing Potion"]),
    ]
    
    after_combat = wizard.execute_parallel(combat_operations)
    
    print(f"After combat:")
    print(f"  HP: {after_combat['hp']}/{after_combat['max_hp']}")
    print(f"  3rd level slots: {after_combat.get_variable('spell_slots.3')}")
    print(f"  Equipment: {after_combat.get_variable('equipment.misc')}")


def example_error_handling():
    """Demonstrate error handling patterns."""
    print("\n=== Error Handling Patterns ===")
    
    context = GrimoireContext({"valid_key": "valid_value"})
    
    # Safe access with defaults
    safe_value = context.get_variable("missing.path", "default_value")
    print(f"Safe access with default: {safe_value}")
    
    # Check before access
    if context.has_variable("valid_key"):
        value = context["valid_key"]
        print(f"Safe existing key access: {value}")
    
    # Handle missing keys gracefully
    try:
        missing = context["definitely_missing"]
    except KeyError:
        print("KeyError handled gracefully for missing key")
    
    # Path access error handling
    nested_value = context.get_variable("missing.nested.path")
    print(f"Missing nested path returns: {nested_value}")


def main():
    """Run all advanced feature examples."""
    print("GrimoireContext - Advanced Features")
    print("=" * 50)
    
    try:
        example_template_resolution()
        example_complex_hierarchy()
        example_parallel_execution()
        example_real_world_rpg_scenario()
        example_error_handling()
        
        print("\n✅ All advanced examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in advanced examples: {e}")
        raise


if __name__ == "__main__":
    main()
