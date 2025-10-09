# Grimoire Context

[![Tests](https://github.com/wyrdbound/grimoire-context/workflows/Tests/badge.svg)](https://github.com/wyrdbound/grimoire-context/actions)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**Immutable, hierarchical context management for the Grimoire tabletop RPG engine.**

Grimoire Context provides a robust, thread-safe context management system designed for complex game state management. It combines the power of immutable data structures with intuitive dict-like interfaces and advanced features like hierarchical scoping and parallel execution.

## ✨ Features

- **🔒 Immutable by Design**: All operations return new context instances, ensuring thread safety and preventing accidental state mutations
- **🏗️ Hierarchical Scoping**: Create child contexts that inherit from parents with proper variable shadowing
- **🎯 Dot Notation Paths**: Access and modify nested data using intuitive dot notation (`character.stats.hp`)
- **📖 Dict-like Interface**: Familiar Python dictionary operations while maintaining immutability
- **🔧 Template Resolution**: Pluggable template system for dynamic content generation
- **⚡ Parallel Execution**: Thread-safe concurrent operations with intelligent conflict detection
- **🛡️ Type Safe**: Full type hints and protocol-based design for better development experience

## 🚀 Quick Start

### Installation

```bash
pip install grimoire-context
```

### Basic Usage

```python
from grimoire_context import GrimoireContext

# Create a context with initial data
context = GrimoireContext({
    'player': 'Alice',
    'character': {
        'name': 'Aragorn',
        'hp': 100,
        'mp': 50
    }
})

# Immutable operations - original context unchanged
new_context = context.set('round', 1)
updated_hp = context.set_variable('character.hp', 85)

print(context['character']['hp'])      # 100 (original unchanged)
print(updated_hp['character']['hp'])   # 85 (new context)

# Dict-like interface
print('player' in context)             # True
print(list(context.keys()))            # ['player', 'character']
```

### Hierarchical Contexts

```python
# Create parent context (global game state)
game_state = GrimoireContext({
    'system': 'grimoire',
    'version': '1.0',
    'difficulty': 'normal'
})

# Create child context (player-specific)
player_context = game_state.create_child_context({
    'player_id': 'alice',
    'character': 'warrior'
})

# Child inherits from parent
print(player_context['system'])        # 'grimoire' (from parent)
print(player_context['player_id'])     # 'alice' (from child)

# Variable shadowing
session = player_context.set('difficulty', 'hard')
print(session['difficulty'])           # 'hard' (shadows parent)
print(game_state['difficulty'])        # 'normal' (parent unchanged)
```

### Advanced Path Operations

```python
context = GrimoireContext({
    'character': {
        'stats': {'str': 15, 'dex': 12},
        'inventory': ['sword', 'potion']
    }
})

# Nested modifications
boosted = context.set_variable('character.stats.str', 18)
new_item = context.set_variable('character.inventory', ['sword', 'potion', 'shield'])

# Path queries
has_dex = context.has_variable('character.stats.dex')  # True
missing = context.get_variable('character.stats.con', 10)  # 10 (default)

# Delete nested paths
no_inventory = context.delete_variable('character.inventory')
```

### Parallel Execution

```python
def buff_strength(ctx):
    current = ctx.get_variable('character.stats.str', 10)
    return ctx.set_variable('character.stats.str', current + 2)

def buff_dexterity(ctx):
    current = ctx.get_variable('character.stats.dex', 10)
    return ctx.set_variable('character.stats.dex', current + 2)

def heal_character(ctx):
    return ctx.set_variable('character.hp', 100)

# Execute multiple operations concurrently
operations = [buff_strength, buff_dexterity, heal_character]
result = context.execute_parallel(operations)

# All changes applied atomically
print(result.get_variable('character.stats.str'))  # Original + 2
print(result.get_variable('character.stats.dex'))  # Original + 2
print(result.get_variable('character.hp'))         # 100
```

#### Conflict Resolution and Merge Semantics

When using `execute_parallel()`, GrimoireContext merges results using these semantics:

- **None values**: Treated as "no change" - will not overwrite existing values
- **Explicit removal**: Use `discard()` or `delete_variable()` to explicitly remove values
- **Conflicts**: Operations modifying the same path will raise `ContextMergeError`
- **Nested objects**: Deep merged recursively with the same semantics

**Examples:**

```python
# ✓ This works - different variables in same object
ctx = GrimoireContext({'stats': {'hp': None, 'mp': None}})

def set_hp(ctx): 
    return ctx.set_variable('stats.hp', 100)

def set_mp(ctx): 
    return ctx.set_variable('stats.mp', 50)

result = ctx.execute_parallel([set_hp, set_mp])
# Result: {'stats': {'hp': 100, 'mp': 50}} - Both values preserved

# ✗ This raises error - same variable modified
def set_hp_100(ctx): 
    return ctx.set_variable('stats.hp', 100) 

def set_hp_200(ctx): 
    return ctx.set_variable('stats.hp', 200)

ctx.execute_parallel([set_hp_100, set_hp_200])  # ContextMergeError

# To explicitly remove a value, use delete methods
def remove_hp(ctx): 
    return ctx.delete_variable('stats.hp')
```

### Template Resolution

```python
from grimoire_context import GrimoireContext

class GameTemplateResolver:
    def resolve_template(self, template: str, context_dict: dict) -> str:
        # Simple template replacement
        import re
        def replace_var(match):
            var_name = match.group(1)
            return str(context_dict.get(var_name, f'<{var_name}>'))
        return re.sub(r'{{(\w+)}}', replace_var, template)

context = GrimoireContext({'player': 'Alice', 'hp': 75})
context = context.set_template_resolver(GameTemplateResolver())

message = context.resolve_template("{{player}} has {{hp}} health remaining")
print(message)  # "Alice has 75 health remaining"
```

## 📚 Core Concepts

### Immutability

Every operation on a `GrimoireContext` returns a new instance. The original context is never modified:

```python
original = GrimoireContext({'score': 100})
modified = original.set('score', 200)

print(original['score'])   # 100 (unchanged)
print(modified['score'])   # 200 (new instance)
print(original is modified)  # False
```

### Context IDs

Each context has a unique identifier that changes when the context is modified:

```python
context = GrimoireContext({'data': 'value'})
original_id = context.context_id

new_context = context.set('data', 'new_value')
new_id = new_context.context_id
print(original_id != new_id)  # True
```

### Error Handling

The package provides specific exceptions for different error conditions:

```python
from grimoire_context import (
    InvalidContextOperation,
    ContextMergeError,
    TemplateError
)

try:
    context['key'] = 'value'  # Direct assignment forbidden
except InvalidContextOperation:
    print("Use .set() method instead")

try:
    context.resolve_template("{{missing_var}}")
except TemplateError:
    print("Template resolution failed")
```

## 🔧 API Reference

### GrimoireContext

#### Constructor

```python
GrimoireContext(data=None, parent=None, template_resolver=None, context_id=None)
```

#### Core Methods

- `set(key, value)` - Return new context with key set to value
- `discard(key)` - Return new context with key removed
- `update(mapping)` - Return new context with multiple key-value pairs updated
- `copy(new_id=None)` - Create a copy of the context

#### Path Operations

- `set_variable(path, value)` - Set value using dot notation path
- `get_variable(path, default=None)` - Get value using dot notation path
- `has_variable(path)` - Check if path exists
- `delete_variable(path)` - Delete value at path

#### Hierarchical Operations

- `create_child_context(data=None)` - Create child context
- `local_data()` - Get only local (non-inherited) data

#### Template Operations

- `set_template_resolver(resolver)` - Set template resolver
- `resolve_template(template)` - Resolve template string

#### Parallel Operations

- `execute_parallel(operations)` - Execute operations concurrently

#### Dict Interface

- `[key]`, `get()`, `keys()`, `values()`, `items()`, `len()`, `iter()`, `in`

## 🧪 Development

### Setup

```bash
git clone https://github.com/wyrdbound/grimoire-context.git
cd grimoire-context
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=grimoire_context

# Run specific test file
pytest tests/test_context.py
```

### Code Quality

```bash
# Linting and formatting
ruff check .
ruff format .

# Type checking
mypy src/
```

## 📋 Requirements

- Python 3.8+
- pyrsistent >= 0.19.0

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 The Wyrd One

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate and follow the existing code style.

If you have questions about the project, please contact: wyrdbound@proton.me

## 🎯 Use Cases

Grimoire Context is particularly well-suited for:

- **Game State Management**: Track character stats, inventory, and world state
- **Rule Engine Contexts**: Manage rule evaluation environments with scoping
- **Template Systems**: Dynamic content generation with variable substitution
- **Configuration Management**: Hierarchical configuration with inheritance
- **Concurrent Processing**: Thread-safe operations on shared state

## 🏗️ Architecture

The package is built on several key components:

- **Immutable Data Layer**: Uses `pyrsistent.PMap` for structural sharing and efficiency
- **Hierarchical Chain**: `collections.ChainMap` provides parent-child relationships
- **Path Resolution**: Custom dot notation parser for nested access
- **Conflict Detection**: Sophisticated merge logic for parallel operations
- **Protocol Design**: Clean interfaces for extensibility

## 📈 Performance

- **Memory Efficient**: Structural sharing means copying contexts is fast and memory-light
- **Thread Safe**: Immutable design eliminates race conditions
- **Scalable**: Hierarchical design supports deep context chains efficiently
- **Optimized Paths**: Dot notation operations are optimized for common access patterns
