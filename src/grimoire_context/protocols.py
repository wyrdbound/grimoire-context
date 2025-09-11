"""Protocol definitions for Grimoire Context package."""

from typing import Any, Dict, Protocol


class TemplateResolver(Protocol):
    """Protocol for injected template resolvers.

    This protocol defines the interface that template resolvers must implement
    to be used with GrimoireContext. It allows for dependency injection of
    template resolution functionality without coupling the context to specific
    template engines.
    """

    def resolve_template(self, template_str: str, context_dict: Dict[str, Any]) -> Any:
        """Resolve a template string using the provided context.

        Args:
            template_str: The template string to resolve (e.g., Jinja2 template)
            context_dict: Dictionary of context variables to use for resolution

        Returns:
            The resolved template result (type depends on template content)

        Raises:
            TemplateError: If template resolution fails
        """
        ...
