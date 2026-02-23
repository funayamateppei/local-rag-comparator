"""Prompt & Template domain model.

Defines the PromptTemplate value object and PromptType enum used across
the RAG comparison pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PromptType(Enum):
    """Supported prompt categories for the RAG pipeline."""

    ENTITY_EXTRACTION = "entity_extraction"
    SEARCH_QUERY = "search_query"
    SUMMARIZATION = "summarization"


@dataclass(frozen=True)
class PromptTemplate:
    """Immutable value object representing a prompt template.

    Attributes:
        name: Human-readable identifier for the prompt.
        template: The template string with ``{{variable}}`` placeholders.
        version: Semantic version of the prompt template.
        variables: List of variable names expected by the template.
    """

    name: str
    template: str
    version: str
    variables: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Prompt name cannot be empty")
        if not self.template:
            raise ValueError("Prompt template cannot be empty")

    def render(self, **kwargs: Any) -> str:
        """Render the template by substituting ``{{variable}}`` placeholders.

        Args:
            **kwargs: Variable name/value pairs to substitute.

        Returns:
            The rendered template string.

        Raises:
            ValueError: If any declared variable is not provided in *kwargs*.
        """
        missing = [v for v in self.variables if v not in kwargs]
        if missing:
            raise ValueError(f"Missing required variables: {missing}")
        result = self.template
        for key, value in kwargs.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result
