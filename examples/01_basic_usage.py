#!/usr/bin/env python3
"""
Basic GrimoireContext Usage Examples

This example demonstrates the fundamental features of grimoire-context:
- Creating contexts with initial data
- Immutable operations (set, discard, update)
- Dict-like interface usage
- Basic hierarchical contexts
"""

from grimoire_context import GrimoireContext


def example_basic_operations():
    """Demonstrate basic context operations."""
    print("=== Basic Context Operations ===")
    
    # Create a context with initial data
    context = GrimoireContext({
        "player_name": "Alice", 
        "level": 5,
        "health": 100,
        "class": "wizard"
    })
    
    print(f"Initial context: {dict(context)}")
    print(f"Context size: {len(context)} variables")
    
    # Immutable set operation - returns new context
    updated_context = context.set_variable("health", 85)
    print(f"After updating health to 85:")
    print(f"  Original: health = {context['health']}")  # Still 100
    print(f"  Updated:  health = {updated_context['health']}")  # Now 85
    
    # Add new variable
    with_mana = updated_context.set_variable("mana", 50)
    print(f"Added mana: {dict(with_mana)}")
    
    # Bulk update
    bulk_updated = with_mana.update({
        "experience": 1200,
        "location": "tavern",
        "gold": 150
    })
    print(f"After bulk update: {dict(bulk_updated)}")
    
    # Remove variable
    without_gold = bulk_updated.discard("gold") 
    print(f"After removing gold: {dict(without_gold)}")


def example_dict_interface():
    """Demonstrate dict-like interface usage."""
    print("\n=== Dict-like Interface ===")
    
    context = GrimoireContext({
        "inventory": {
            "weapons": ["sword", "dagger"],
            "potions": {"health": 3, "mana": 1}
        },
        "stats": {"strength": 15, "wisdom": 18}
    })
    
    # Dictionary-style access
    print(f"Player strength: {context['stats']['strength']}")
    print(f"Health potions: {context['inventory']['potions']['health']}")
    
    # Check if keys exist
    print(f"Has 'inventory': {'inventory' in context}")
    print(f"Has 'spells': {'spells' in context}")
    
    # Get with default
    spells = context.get("spells", [])
    print(f"Spells (with default): {spells}")
    
    # Iterate over items
    print("All variables:")
    for key, value in context.items():
        print(f"  {key}: {value}")


def example_path_operations():
    """Demonstrate dot notation path access."""
    print("\n=== Path Operations ===")
    
    context = GrimoireContext({
        "character": {
            "name": "Bob",
            "stats": {"str": 14, "dex": 16, "int": 12},
            "equipment": {
                "weapon": {"name": "Iron Sword", "damage": 8},
                "armor": {"name": "Leather Armor", "defense": 3}
            }
        }
    })
    
    # Access nested values with dot notation
    weapon_name = context.get_variable("character.equipment.weapon.name")
    print(f"Weapon name: {weapon_name}")
    
    dexterity = context.get_variable("character.stats.dex")
    print(f"Dexterity: {dexterity}")
    
    # Set nested values
    upgraded_weapon = context.set_variable("character.equipment.weapon.damage", 12)
    print(f"Upgraded weapon damage: {upgraded_weapon.get_variable('character.equipment.weapon.damage')}")
    
    # Add new nested structure
    with_spells = upgraded_weapon.set_variable("character.spells.fireball", {
        "level": 2,
        "damage": "2d6",
        "mana_cost": 15
    })
    
    fireball_damage = with_spells.get_variable("character.spells.fireball.damage")
    print(f"Fireball damage: {fireball_damage}")
    
    # Check if nested path exists
    has_fireball = with_spells.has_variable("character.spells.fireball")
    has_lightning = with_spells.has_variable("character.spells.lightning")
    print(f"Has fireball spell: {has_fireball}")
    print(f"Has lightning spell: {has_lightning}")


def example_basic_hierarchy():
    """Demonstrate basic hierarchical contexts."""
    print("\n=== Basic Hierarchical Contexts ===")
    
    # Global game state
    global_context = GrimoireContext({
        "game_version": "1.0.0",
        "difficulty": "normal",
        "debug_mode": False
    })
    
    print(f"Global context: {dict(global_context)}")
    
    # Character-specific context inherits from global
    character_context = global_context.create_child_context({
        "name": "Charlie",
        "class": "rogue",
        "level": 3
    })
    
    print(f"Character context keys: {list(character_context.keys())}")
    print(f"Character can access game_version: {character_context['game_version']}")
    print(f"Character class: {character_context['class']}")
    
    # Scene-specific context inherits from character
    scene_context = character_context.create_child_context({
        "location": "dungeon",
        "light_level": "dim",
        "debug_mode": True  # Override global setting
    })
    
    print(f"Scene context keys: {list(scene_context.keys())}")
    print(f"Scene debug_mode (overridden): {scene_context['debug_mode']}")
    print(f"Scene can access character name: {scene_context['name']}")
    print(f"Scene can access global difficulty: {scene_context['difficulty']}")


def example_context_copying():
    """Demonstrate context copying and independence."""
    print("\n=== Context Copying and Independence ===")
    
    original = GrimoireContext({
        "base_stats": {"hp": 100, "mp": 50},
        "equipment": ["sword", "shield"]
    })
    
    # Create a copy
    copy1 = original.copy()
    copy2 = original.copy()
    
    # Modify copies independently  
    copy1_modified = copy1.set_variable("base_stats.hp", 120)
    copy2_modified = copy2.set_variable("equipment", ["bow", "arrows"])
    
    print("Original context unchanged:")
    print(f"  HP: {original.get_variable('base_stats.hp')}")
    print(f"  Equipment: {original['equipment']}")
    
    print("Copy 1 (HP modified):")
    print(f"  HP: {copy1_modified.get_variable('base_stats.hp')}")
    print(f"  Equipment: {copy1_modified['equipment']}")
    
    print("Copy 2 (equipment modified):")
    print(f"  HP: {copy2_modified.get_variable('base_stats.hp')}")
    print(f"  Equipment: {copy2_modified['equipment']}")


def main():
    """Run all basic usage examples."""
    print("GrimoireContext - Basic Usage Examples")
    print("=" * 50)
    
    try:
        example_basic_operations()
        example_dict_interface()
        example_path_operations()
        example_basic_hierarchy()
        example_context_copying()
        
        print("\n✅ All basic examples completed successfully!")
        
    except Exception as e:
        print(f"❌ Error in basic examples: {e}")
        raise


if __name__ == "__main__":
    main()
