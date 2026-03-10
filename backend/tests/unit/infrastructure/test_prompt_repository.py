"""Tests for PromptRepository infrastructure adapter.

TDD Red-Green: these tests verify that PromptRepository correctly
implements IPromptRepository by delegating to PromptLoader and the
real YAML prompt files.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from src.domain.models.prompt import PromptTemplate, PromptType
from src.domain.repositories import IPromptRepository
from src.infrastructure.prompt_repository import PromptRepository

# ---------------------------------------------------------------------------
# Interface compliance
# ---------------------------------------------------------------------------


class TestPromptRepositoryInterface:
    """PromptRepository must implement IPromptRepository."""

    def test_is_instance_of_iprompt_repository(self) -> None:
        repo = PromptRepository()
        assert isinstance(repo, IPromptRepository)

    def test_has_load_method(self) -> None:
        repo = PromptRepository()
        assert callable(getattr(repo, "load", None))


# ---------------------------------------------------------------------------
# Loading each prompt type from real YAML files
# ---------------------------------------------------------------------------


class TestPromptRepositoryLoadEntityExtraction:
    """Loading entity_extraction prompt from YAML."""

    def test_returns_prompt_template(self) -> None:
        repo = PromptRepository()
        result = repo.load(PromptType.ENTITY_EXTRACTION)
        assert isinstance(result, PromptTemplate)

    def test_has_correct_name(self) -> None:
        repo = PromptRepository()
        result = repo.load(PromptType.ENTITY_EXTRACTION)
        assert result.name == "entity_extraction"

    def test_has_correct_version(self) -> None:
        repo = PromptRepository()
        result = repo.load(PromptType.ENTITY_EXTRACTION)
        assert result.version == "1.0"

    def test_has_correct_variables(self) -> None:
        repo = PromptRepository()
        result = repo.load(PromptType.ENTITY_EXTRACTION)
        assert result.variables == ["text", "language"]

    def test_template_contains_placeholders(self) -> None:
        repo = PromptRepository()
        result = repo.load(PromptType.ENTITY_EXTRACTION)
        assert "{{text}}" in result.template
        assert "{{language}}" in result.template

    def test_render_with_variables(self) -> None:
        repo = PromptRepository()
        result = repo.load(PromptType.ENTITY_EXTRACTION)
        rendered = result.render(text="サンプルテキスト", language="ja")
        assert "サンプルテキスト" in rendered
        assert "ja" in rendered


class TestPromptRepositoryLoadSearchQuery:
    """Loading search_query prompt from YAML."""

    def test_returns_prompt_template(self) -> None:
        repo = PromptRepository()
        result = repo.load(PromptType.SEARCH_QUERY)
        assert isinstance(result, PromptTemplate)

    def test_has_correct_name(self) -> None:
        repo = PromptRepository()
        result = repo.load(PromptType.SEARCH_QUERY)
        assert result.name == "search_query"

    def test_has_correct_version(self) -> None:
        repo = PromptRepository()
        result = repo.load(PromptType.SEARCH_QUERY)
        assert result.version == "1.0"

    def test_has_correct_variables(self) -> None:
        repo = PromptRepository()
        result = repo.load(PromptType.SEARCH_QUERY)
        assert result.variables == ["query", "language"]

    def test_template_contains_placeholders(self) -> None:
        repo = PromptRepository()
        result = repo.load(PromptType.SEARCH_QUERY)
        assert "{{query}}" in result.template
        assert "{{language}}" in result.template

    def test_render_with_variables(self) -> None:
        repo = PromptRepository()
        result = repo.load(PromptType.SEARCH_QUERY)
        rendered = result.render(query="テストクエリ", language="ja")
        assert "テストクエリ" in rendered
        assert "ja" in rendered


class TestPromptRepositoryLoadSummarization:
    """Loading summarization prompt from YAML."""

    def test_returns_prompt_template(self) -> None:
        repo = PromptRepository()
        result = repo.load(PromptType.SUMMARIZATION)
        assert isinstance(result, PromptTemplate)

    def test_has_correct_name(self) -> None:
        repo = PromptRepository()
        result = repo.load(PromptType.SUMMARIZATION)
        assert result.name == "summarization"

    def test_has_correct_version(self) -> None:
        repo = PromptRepository()
        result = repo.load(PromptType.SUMMARIZATION)
        assert result.version == "1.0"

    def test_has_correct_variables(self) -> None:
        repo = PromptRepository()
        result = repo.load(PromptType.SUMMARIZATION)
        assert result.variables == ["text", "language"]

    def test_template_contains_placeholders(self) -> None:
        repo = PromptRepository()
        result = repo.load(PromptType.SUMMARIZATION)
        assert "{{text}}" in result.template
        assert "{{language}}" in result.template

    def test_render_with_variables(self) -> None:
        repo = PromptRepository()
        result = repo.load(PromptType.SUMMARIZATION)
        rendered = result.render(text="要約対象テキスト", language="ja")
        assert "要約対象テキスト" in rendered
        assert "ja" in rendered


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestPromptRepositoryErrors:
    """Error cases for PromptRepository."""

    def test_missing_prompt_file_raises_file_not_found(self, tmp_path: Path) -> None:
        """Loading from an empty directory should raise FileNotFoundError."""
        repo = PromptRepository(prompts_dir=tmp_path)
        with pytest.raises(FileNotFoundError):
            repo.load(PromptType.ENTITY_EXTRACTION)

    def test_custom_prompts_dir(self, tmp_path: Path) -> None:
        """PromptRepository should accept a custom prompts directory."""
        repo = PromptRepository(prompts_dir=tmp_path)
        with pytest.raises(FileNotFoundError):
            repo.load(PromptType.SEARCH_QUERY)
