# AI Guidance

Always remember the following points as you are working on this code base:

1. Use the virtual env in the project root (`source .venv/bin/activate && <your_command>`)

2. Prefer explicit errors over fallbacks when fallbacks would mask issues. We want to fix issues so we can have a stable system.

3. Follow good software development practices (like SOLID).

4. Simpler is better.

5. Remember that the purpose of this package is to provide a flexible and reusable model implementation for the Wyrdbound engine. Avoid adding special-cases or hack fixes simply to get around issues.

6. Do NOT make bandaid fixes that break the rearchitecture goals for Wyrdbound Context. Always respect the architectural boundaries.

7. After all code changes, run `ruff check src/ tests/ --fix`, `ruff format src/ tests/`, and `mypy src/` to ensure code quality is retained in an interative manner.

8. Avoid making lines longer than 88 characters (E501 ruff check).
