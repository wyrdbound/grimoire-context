# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **Nested Path Setting on Objects**: Fixed critical issue where `set_variable()` with nested paths (e.g., `"object.property"`) would overwrite non-dict objects with empty dicts, losing all object data. The path resolver now intelligently handles custom objects:
  - Tries `__setitem__()` first for dict-like objects
  - Falls back to `setattr()` for objects with attributes  
  - Only converts to dict as last resort with warning
  - Preserves object types and all existing data
  - Maintains immutability using deep copies
  
### Changed

- **Path Resolution Enhancement**: `get_nested_path()` now supports attribute access on objects in addition to dict/PMap access, enabling seamless navigation through mixed dict/object hierarchies.

## [0.3.0] - 2025-10-08

### Fixed

- **Parallel Execution Bug**: Fixed issue where `execute_parallel()` operations would lose changes when merging contexts containing `None` values. `None` values are now treated as "no change" during merge operations, preserving all parallel modifications. Use `discard()` or `delete_variable()` methods to explicitly remove values from contexts.

### Changed

- **Merge Semantics**: `None` values in context merging are now treated as "no change" rather than explicit assignments, improving parallel execution behavior and semantic clarity.

## [0.2.0] - 2025-09-12

### Added

- Integration with `grimoire-logging` package for flexible dependency injection logging
- Strategic logging throughout the library:
  - INFO-level logs for system initialization and successful parallel operations
  - DEBUG-level logs for context operations, child creation, and path resolution
  - WARNING-level logs for missing variables, path overwrites, and merge conflicts
  - ERROR-level logs for template resolution failures and parallel operation errors
- Comprehensive logging examples in `examples/` directory
- Updated LOGGING.md with grimoire-context specific configuration guidance
- Logger hierarchy with dedicated loggers for different subsystems
- Comprehensive library examples demonstrating core functionality
- Real-world usage patterns and integration examples
- Consolidated logging example with practical scenarios

### Changed

- Replaced custom logging implementation with `grimoire-logging` dependency
- Updated all logging calls to use appropriate namespaces (`grimoire_context.*`)
- Enhanced error reporting with more detailed context information
- License changed from proprietary to MIT License
- Reorganized examples directory to focus on library functionality rather than just logging
- Improved example documentation and usage patterns

### Dependencies

- Added `grimoire-logging>=0.1.0` as a required dependency

## [0.0.1] - 2025-09-11

### Added

- Initial release
- Complete immutable context management system with structural sharing
- Hierarchical context scoping with parent-child relationships
- Dot notation path access for nested data manipulation
- Dict-like interface for familiar Python operations
- Template resolution system with pluggable resolvers
- Parallel execution support with conflict detection
- Thread-safe operations through immutable design
- Comprehensive type hints and protocol-based architecture
- Full test suite with unit, integration, and parallel execution tests
- Support for Python 3.8+ with modern tooling
- Development tools integration (pytest, mypy, ruff)
- Extensive documentation with examples and use cases
