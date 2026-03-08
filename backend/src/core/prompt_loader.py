"""Prompt loader that reads YAML prompt definitions from disk.

Provides a single entry-point for loading prompt templates by
:class:`~src.domain.models.prompt.PromptType`.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from src.domain.models.prompt import PromptTemplate, PromptType


class PromptLoader:
    """Load :class:`PromptTemplate` instances from YAML files.

    Args:
        prompts_dir: Directory containing ``<prompt_type>.yaml`` files.
            Defaults to the ``prompts/`` directory next to this module.
    """

    def __init__(self, prompts_dir: Path | None = None) -> None:
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent / "prompts"
        self._prompts_dir = prompts_dir

    def load(self, prompt_type: PromptType) -> PromptTemplate:
        """Load a prompt template for the given *prompt_type*.

        Args:
            prompt_type: The category of prompt to load.

        Returns:
            A fully-initialised :class:`PromptTemplate`.

        Raises:
            FileNotFoundError: If the YAML file does not exist.
            ValueError: If the YAML is malformed or missing required fields.
        """
        file_path = self._prompts_dir / f"{prompt_type.value}.yaml"
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {file_path}")

        with open(file_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid YAML format in {file_path}")

        required_fields = ["name", "template", "version"]
        for field_name in required_fields:
            if field_name not in data:
                raise ValueError(f"Missing required field '{field_name}' in {file_path}")

        return PromptTemplate(
            name=data["name"],
            template=data["template"],
            version=data["version"],
            variables=data.get("variables", []),
        )
