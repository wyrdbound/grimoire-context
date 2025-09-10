# Logging in Wyrdbound Context

This document describes how to configure and use logging in the `wyrdbound-context` library.

## Overview

The `wyrdbound-context` library uses dependency injection for logging, allowing applications to choose their preferred logging implementation. You can either use the standard Python `logging` module or inject your own custom logger implementation.

## Basic Usage

### Using Standard Python Logging

By default, the library uses Python's standard `logging` module:

```python
import logging
from wyrdbound_context import WyrdboundContext

# Configure standard logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('wyrdbound_context')
logger.setLevel(logging.DEBUG)

# Create context - will log using standard logging
context = WyrdboundContext({'key': 'value'})
```

### Injecting a Custom Logger

You can inject your own logger implementation that follows the `LoggerProtocol`:

```python
from wyrdbound_context import inject_logger, LoggerProtocol, WyrdboundContext

class MyLogger:
    def debug(self, message: str) -> None:
        print(f"DEBUG: {message}")

    def info(self, message: str) -> None:
        print(f"INFO: {message}")

    def warning(self, message: str) -> None:
        print(f"WARNING: {message}")

    def error(self, message: str) -> None:
        print(f"ERROR: {message}")

# Inject your custom logger
inject_logger(MyLogger())

# Now all logging will use your custom logger
context = WyrdboundContext({'key': 'value'})
```

### Resetting to Standard Logging

To return to standard Python logging:

```python
from wyrdbound_context import inject_logger

# Reset to standard logging
inject_logger(None)
```

## Logger Protocol

Custom loggers must implement the `LoggerProtocol` interface:

```python
from typing import Protocol

class LoggerProtocol(Protocol):
    def debug(self, message: str) -> None: ...
    def info(self, message: str) -> None: ...
    def warning(self, message: str) -> None: ...
    def error(self, message: str) -> None: ...
```

## What Gets Logged

The library logs the following events:

### Debug Level

- **Context Creation**: When new contexts are created

  ```
  Created WyrdboundContext 'abc123' with 2 local keys
  Created WyrdboundContext 'def456' with 1 local keys (with parent)
  ```

- **Template Resolution**: When templates are being resolved
  ```
  Resolving template in context 'abc123': Hello {{name}}
  ```

### Warning Level

- **Merge Conflicts**: When parallel operations conflict
  ```
  Path conflicts detected in parallel merge: ['shared_key', 'nested.value']
  ```

### Error Level

- **Template Resolution Failures**: When template resolution fails

  ```
  Template resolution failed in context 'abc123': Template syntax error
  ```

- **Path Resolution Failures**: When nested path operations fail
  ```
  Failed to set nested path 'invalid.path': Cannot traverse non-dict value
  ```

## Configuration Examples

### Structured Logging with JSON

```python
import json
import sys
from wyrdbound_context import inject_logger

class JSONLogger:
    def _log(self, level: str, message: str):
        log_entry = {
            "timestamp": "2025-01-01T12:00:00Z",
            "level": level,
            "logger": "wyrdbound_context",
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
from wyrdbound_context import inject_logger

class FilteringLogger:
    def __init__(self, base_logger):
        self.base_logger = base_logger
        self.ignored_patterns = ["Created WyrdboundContext"]

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
standard_logger = logging.getLogger('wyrdbound_context')
inject_logger(FilteringLogger(standard_logger))
```

### Integration with Third-Party Logging

```python
# Example with structlog
import structlog
from wyrdbound_context import inject_logger

class StructlogAdapter:
    def __init__(self):
        self.logger = structlog.get_logger("wyrdbound_context")

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
from wyrdbound_context import inject_logger

def setup_logging():
    """Set up logging for production use."""
    level = os.getenv('WYRDBOUND_LOG_LEVEL', 'INFO').upper()

    logging.basicConfig(
        level=getattr(logging, level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('wyrdbound.log')
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
