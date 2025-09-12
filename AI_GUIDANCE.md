# AI Guidance

Always remember the following points as you are working on this code base:

1. Use the virtual env in the project root (`source .venv/bin/activate && <your_command>`)

2. Prefer explicit errors over fallbacks when fallbacks would mask issues. We want to fix issues so we can have a stable system.

3. Follow good software development practices (like SOLID).

4. Simpler is better.

5. Remember the purpose of this package is to provide its functionality in a clear and maintainable manner. Avoid adding special-cases or hack fixes simply to get around issues.

6. Do NOT make bandaid fixes that break the rearchitecture goals for the library. Always respect the architectural boundaries.

7. After all code changes, run `source .venv/bin/activate && ruff format src/ tests/ && ruff check src/ tests/ --fix && mypy src/` to ensure code quality is retained in an iterative manner.

8. Avoid making lines longer than 88 characters (E501 ruff check).

9. This is a logging library - it should be robust, reliable, and have minimal dependencies. Don't add features that would compromise these principles.

10. Thread safety is critical - all public APIs must be thread-safe and work correctly in concurrent environments.
