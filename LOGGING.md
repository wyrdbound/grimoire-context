# Logging Configuration for Grimoire Context

The `grimoire-context` library uses `grimoire-logging` for flexible logging with dependency injection capabilities. This allows you to easily inject custom logger implementations or use standard Python logging.

## Overview

The `grimoire-context` library provides comprehensive logging throughout its operations using the `grimoire_context` logger namespace with child loggers for different components. All logging uses the `grimoire-logging` package, which provides:

- **Dependency Injection**: Inject custom logger implementations at runtime
- **Thread Safety**: All operations are thread-safe for concurrent environments
- **Fallback Support**: Automatically falls back to Python's standard logging
- **Zero Dependencies**: Core functionality requires no external dependencies beyond grimoire-logging
- **Protocol-Based**: Clean interface definition using Python protocols

## Quick Setup

The library uses the logger namespace `grimoire_context` with child loggers for different components. You can configure logging in several ways:

### Method 1: Standard Python Logging (Default)

By default, grimoire-context falls back to Python's standard logging. Configure it before importing the library:

```python
import logging
import sys

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Optionally adjust the grimoire-context logger level
logging.getLogger('grimoire_context').setLevel(logging.DEBUG)

# Now import and use the library
from grimoire_context import GrimoireContext
context = GrimoireContext({'player': 'Alice'})
```

### Method 2: Dependency Injection with Custom Logger

Use grimoire-logging's dependency injection to provide your own logger implementation:

```python
from grimoire_context import inject_logger, GrimoireContext

# Create a custom logger
class MyCustomLogger:
    def debug(self, msg: str, *args, **kwargs) -> None:
        print(f"🐛 DEBUG: {msg}")

    def info(self, msg: str, *args, **kwargs) -> None:
        print(f"📝 INFO: {msg}")

    def warning(self, msg: str, *args, **kwargs) -> None:
        print(f"⚠️ WARNING: {msg}")

    def error(self, msg: str, *args, **kwargs) -> None:
        print(f"❌ ERROR: {msg}")

    def critical(self, msg: str, *args, **kwargs) -> None:
        print(f"💀 CRITICAL: {msg}")

# Inject your custom logger
inject_logger(MyCustomLogger())

# All grimoire-context logging now uses your custom logger
context = GrimoireContext({'game': 'RPG'})
```

### Method 3: Adapter Pattern for Integration

Create an adapter to integrate with your existing logging infrastructure:

```python
import logging
from grimoire_context import inject_logger

class StandardLoggingAdapter:
    """Adapter to use your existing Python logging setup."""

    def __init__(self, logger_name: str = "myapp.grimoire_context"):
        self.logger = logging.getLogger(logger_name)

    def debug(self, msg: str, *args, **kwargs) -> None:
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        self.logger.critical(msg, *args, **kwargs)

# Use your existing logging configuration
inject_logger(StandardLoggingAdapter())
```

## Logger Hierarchy

The library uses the following logger hierarchy (all under the `grimoire_context` namespace):

- `grimoire_context` - Root library logger
- `grimoire_context.context` - Context operations and lifecycle
- `grimoire_context.merge` - Context merging and parallel execution
- `grimoire_context.path_resolver` - Nested path operations and resolution

You can configure individual subsystems by getting their specific loggers:

```python
import logging

# Configure different levels for different components
logging.getLogger('grimoire_context.context').setLevel(logging.DEBUG)
logging.getLogger('grimoire_context.merge').setLevel(logging.INFO)
logging.getLogger('grimoire_context.path_resolver').setLevel(logging.WARNING)
```

## What Gets Logged

The library logs messages at appropriate levels for different operational scenarios:

### INFO Level Messages

- **System Initialization**: `"Grimoire Context system initialized with N initial variables"`
- **Parallel Operations**: `"Successfully executed N parallel operations and merged results"`

### DEBUG Level Messages

- **Context Creation**: `"Created GrimoireContext 'abc123' with 2 local keys"`
- **Child Context Creation**: `"Created child context 'def456' with 3 variables from parent 'abc123'"`
- **Template Resolution**: `"Resolving template in context 'abc123': Hello {{name}}"`
- **Variable Operations**: `"Setting nested path 'player.stats.hp' with 3 levels"`
- **Bulk Updates**: `"Bulk update of 10 variables in context 'abc123'"`
- **Template Resolver Changes**: `"Template resolver set for context 'abc123': JinjaResolver"`
- **Merge Strategy**: `"Merging 3 contexts with 'last_wins' conflict strategy"`

### WARNING Level Messages

- **Missing Variables**: `"Requested variable 'player.missing' not found in context 'abc123', returning None"`
- **Path Overwrites**: `"Overwriting non-dict value at 'config' to create nested path 'config.setting'"`
- **Merge Conflicts**: `"Path conflicts detected in parallel merge: ['shared_key', 'nested.value']"`

### ERROR Level Messages

- **Template Resolution Failures**: `"Template resolution failed in context 'abc123': Template syntax error"`
- **Path Resolution Failures**: `"Failed to set nested path 'invalid.path': Cannot traverse non-dict value"`
- **Parallel Operation Failures**: `"Parallel context operation failed: ValueError: Invalid operation"`

## Configuration Examples

### Structured Logging with JSON

```python
import json
import sys
from grimoire_context import inject_logger

class JSONLogger:
    def _log(self, level: str, message: str):
        log_entry = {
            "timestamp": "2025-01-01T12:00:00Z",
            "level": level,
            "logger": "grimoire_context",
            "message": message
        }
        print(json.dumps(log_entry), file=sys.stderr)

    def debug(self, message: str) -> None:
        self._log("DEBUG", message)

    def info(self, message: str) -> None:
        self._log("INFO", message)

    def warning(self, message: str) -> None:
        self._log("WARNING", message)

    def error(self, message: str) -> None:
        self._log("ERROR", message)

inject_logger(JSONLogger())
```

### Filtering Specific Messages

```python
from grimoire_context import inject_logger

class FilteringLogger:
    def __init__(self, base_logger):
        self.base_logger = base_logger
        self.ignored_patterns = ["Created GrimoireContext"]

    def _should_log(self, message: str) -> bool:
        return not any(pattern in message for pattern in self.ignored_patterns)

    def debug(self, message: str) -> None:
        if self._should_log(message):
            self.base_logger.debug(message)

    def info(self, message: str) -> None:
        if self._should_log(message):
            self.base_logger.info(message)

    def warning(self, message: str) -> None:
        self.base_logger.warning(message)  # Always log warnings

    def error(self, message: str) -> None:
        self.base_logger.error(message)  # Always log errors

# Use with standard logging
import logging
standard_logger = logging.getLogger('grimoire_context')
inject_logger(FilteringLogger(standard_logger))
```

### Integration with Third-Party Logging

```python
# Example with structlog
import structlog
from grimoire_context import inject_logger

class StructlogAdapter:
    def __init__(self):
        self.logger = structlog.get_logger("grimoire_context")

    def debug(self, message: str) -> None:
        self.logger.debug(message)

    def info(self, message: str) -> None:
        self.logger.info(message)

    def warning(self, message: str) -> None:
        self.logger.warning(message)

    def error(self, message: str) -> None:
        self.logger.error(message)

inject_logger(StructlogAdapter())
```

## Thread Safety

Logger injection is **not thread-safe**. It's recommended to inject your logger once during application startup before creating any threads.

```python
# Good: Inject logger at startup
def main():
    inject_logger(MyLogger())
    # Now safe to use in multiple threads

# Bad: Don't inject loggers in multiple threads simultaneously
def worker_thread():
    inject_logger(SomeLogger())  # Race condition!
```

## Performance Considerations

- **Lazy Evaluation**: Log messages are only formatted when logging is enabled for that level
- **Minimal Overhead**: The library only logs at key operation points
- **Custom Filtering**: Implement filtering in your custom logger to reduce overhead

## Best Practices

1. **Configure Early**: Set up logging before creating any contexts
2. **Use Appropriate Levels**: Debug for detailed tracing, warning/error for issues
3. **Implement Filtering**: Filter out verbose messages in production
4. **Handle Exceptions**: Ensure your logger implementation doesn't raise exceptions
5. **Consider Performance**: Avoid expensive operations in logging methods

## Example: Production Setup

```python
import logging
import os
from grimoire_context import inject_logger

def setup_logging():
    """Set up logging for production use."""
    level = os.getenv('GRIMOIRE_LOG_LEVEL', 'INFO').upper()

    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('grimoire.log')
        ]
    )

    # Use standard logging (inject_logger(None) is the default)
    # But we could inject a custom logger here if needed

# Call during application startup
setup_logging()
```

## Troubleshooting

### No Log Output

- Check that your logger is properly configured
- Verify log levels are set appropriately
- Ensure handlers are attached to the logger

### Too Verbose

- Increase log level filtering
- Implement message filtering in your custom logger
- Use `inject_logger(None)` and configure standard logging filters

### Performance Issues

- Avoid expensive operations in logger methods
- Use log level checks in your custom logger
- Consider asynchronous logging for high-throughput applications
