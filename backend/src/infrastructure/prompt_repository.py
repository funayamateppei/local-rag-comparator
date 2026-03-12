"""PromptRepository - IPromptRepository implementation using PromptLoader."""

from pathlib import Path

from src.core.prompt_loader import PromptLoader
from src.domain.models.prompt import PromptTemplate, PromptType
from src.domain.repositories import IPromptRepository


class PromptRepository(IPromptRepository):
    """Concrete implementation of IPromptRepository using YAML-based PromptLoader."""

    def __init__(self, prompts_dir: Path | None = None) -> None:
        self._loader = PromptLoader(prompts_dir=prompts_dir)

    def load(self, prompt_type: PromptType) -> PromptTemplate:
        return self._loader.load(prompt_type)
