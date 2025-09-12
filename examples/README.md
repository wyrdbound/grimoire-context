# GrimoireContext Examples

This directory contains comprehensive examples demonstrating how to use grimoire-context in various scenarios, from basic operations to real-world integration patterns.

## Examples Overview

### 1. Basic Usage (`01_basic_usage.py`)

Demonstrates fundamental grimoire-context operations:

- Creating contexts with initial data
- Immutable operations (set, discard, update)
- Dict-like interface usage
- Path-based access to nested data
- Basic hierarchical contexts
- Context copying and independence

**Key Features Shown:**

- Context creation and basic CRUD operations
- Variable shadowing in hierarchies
- Dot notation for nested access
- Immutability guarantees

### 2. Advanced Features (`02_advanced_features.py`)

Shows advanced capabilities and patterns:

- Template resolution with custom resolvers
- Complex hierarchical context structures
- Parallel execution with conflict detection
- Error handling patterns
- Real-world RPG scenario simulation

**Key Features Shown:**

- Template string resolution
- Multi-level context hierarchies
- Concurrent operations and merge strategies
- Comprehensive error handling

### 3. Real-World Integration (`03_real_world_integration.py`)

Demonstrates practical integration patterns:

- Web application request context patterns
- Configuration management strategies
- Testing patterns and best practices
- Performance optimization techniques
- Integration best practices and factories

**Key Features Shown:**

- Request/response lifecycle context management
- Environment-specific configuration
- Test context creation and isolation
- Performance benchmarking
- Factory and middleware patterns

### 4. Logging Integration (`logging_integration.py`)

Comprehensive logging integration examples:

- Basic logging setup with standard Python logging
- JSON structured logging for production
- Mock logger injection for testing
- Concurrent logging with thread safety
- Performance monitoring with logging

**Key Features Shown:**

- Standard logging integration
- Custom logger injection
- Structured JSON logging
- Thread-safe concurrent logging

## Running the Examples

Each example can be run independently:

```bash
# Basic usage examples
python examples/01_basic_usage.py

# Advanced features
python examples/02_advanced_features.py

# Real-world integration patterns
python examples/03_real_world_integration.py

# Logging integration
python examples/logging_integration.py
```

All examples include detailed output and explanations of what's happening at each step.

## Quick Start Guide

### Basic Context Operations

```python
from grimoire_context import GrimoireContext

# Create context with initial data
context = GrimoireContext({
    "user": {"name": "Alice", "level": 5},
    "game": {"mode": "adventure"}
})

# Immutable operations return new contexts
updated = context.set_variable("user.level", 6)
print(context.get_variable("user.level"))  # Still 5
print(updated.get_variable("user.level"))   # Now 6

# Hierarchical contexts
child = context.create_child_context({"session": "abc123"})
print(child["user"]["name"])  # "Alice" (inherited)
print(child["session"])       # "abc123" (local)
```

### Path-Based Access

```python
# Access nested data with dot notation
health = context.get_variable("character.stats.health")

# Set nested values
updated = context.set_variable("inventory.gold", 150)

# Check if nested paths exist
has_weapon = context.has_variable("equipment.weapon")
```

### Hierarchical Contexts

```python
# Global application context
app_ctx = GrimoireContext({"app_name": "MyApp", "version": "1.0"})

# Request-specific context
request_ctx = app_ctx.create_child_context({
    "request_id": "req_123",
    "user_id": 456
})

# Route-specific context
route_ctx = request_ctx.create_child_context({
    "controller": "users",
    "action": "profile"
})

# Child contexts can access parent data
print(route_ctx["app_name"])  # "MyApp"
print(route_ctx["user_id"])   # 456
```

### Parallel Operations

```python
# Define operations that can run in parallel
operations = [
    lambda ctx: ctx.set_variable("health", ctx["health"] - 10),
    lambda ctx: ctx.set_variable("mana", ctx["mana"] - 5),
    lambda ctx: ctx.set_variable("experience", ctx["experience"] + 100)
]

# Execute in parallel (with automatic conflict detection)
result = context.execute_parallel(operations)
```

## Integration Patterns

### Web Application Context

```python
# Application-level context
app = GrimoireContext({
    "app_name": "MyWebApp",
    "environment": "production",
    "database_url": "postgresql://..."
})

# Per-request context
def handle_request(request):
    request_ctx = app.create_child_context({
        "request_id": request.id,
        "user_id": request.user.id,
        "timestamp": time.time()
    })

    # Use request_ctx throughout request processing
    return process_with_context(request_ctx)
```

### Configuration Management

```python
# Base configuration
base_config = GrimoireContext({
    "database": {"host": "localhost", "port": 5432},
    "cache": {"enabled": True, "ttl": 3600}
})

# Environment-specific config
prod_config = base_config.create_child_context({
    "database": {"host": "prod-db.company.com"},
    "logging": {"level": "ERROR"}
})
```

### Testing Patterns

```python
def create_test_context(test_name: str, **overrides):
    """Create standardized test context."""
    base = {
        "test_name": test_name,
        "environment": "test",
        "database_url": "sqlite:///:memory:"
    }
    return GrimoireContext({**base, **overrides})

# Use in tests
def test_user_logic():
    ctx = create_test_context("test_user", user_id=123)
    result = my_function(ctx)
    assert result["success"] is True
```

## Best Practices

1. **Use hierarchical contexts** for natural data scoping (app → request → operation)

2. **Leverage path notation** for clean nested data access

3. **Create context factories** for consistent context creation patterns

4. **Use parallel operations** for independent concurrent modifications

5. **Implement proper error handling** with graceful fallbacks

6. **Structure your contexts** to match your application architecture

7. **Test with mock contexts** to ensure proper isolation

## Performance Considerations

- Context operations are optimized with structural sharing
- Hierarchical lookups are efficient through chain maps
- Parallel operations use thread pools for true concurrency
- Path operations are cached for repeated access
- Memory usage is minimized through immutable data structures

## Common Use Cases

- **Web Applications**: Request/response lifecycle management
- **Game Engines**: Character state and world context management
- **Configuration Systems**: Environment and feature flag management
- **Template Engines**: Variable scoping and resolution
- **Workflow Systems**: Step context and state management
- **Testing Frameworks**: Test isolation and mock data management

For more detailed examples and patterns, explore the individual example files!
