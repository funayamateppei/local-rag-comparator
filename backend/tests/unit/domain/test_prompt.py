"""Tests for PromptTemplate domain model and PromptLoader.

TDD Red phase: these tests define the expected behavior of the
PromptTemplate value object, PromptType enum, and PromptLoader utility.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.domain.models.prompt import PromptTemplate, PromptType
from src.core.prompt_loader import PromptLoader


# ---------------------------------------------------------------------------
# PromptType enum
# ---------------------------------------------------------------------------


class TestPromptType:
    """PromptType enum must expose the three supported prompt categories."""

    def test_entity_extraction_value(self) -> None:
        assert PromptType.ENTITY_EXTRACTION.value == "entity_extraction"

    def test_search_query_value(self) -> None:
        assert PromptType.SEARCH_QUERY.value == "search_query"

    def test_summarization_value(self) -> None:
        assert PromptType.SUMMARIZATION.value == "summarization"

    def test_enum_members_count(self) -> None:
        """Exactly three members should exist."""
        assert len(PromptType) == 3


# ---------------------------------------------------------------------------
# PromptTemplate dataclass creation
# ---------------------------------------------------------------------------


class TestPromptTemplateCreation:
    """PromptTemplate must be a frozen (immutable) dataclass with validation."""

    def test_create_with_all_fields(self) -> None:
        pt = PromptTemplate(
            name="test_prompt",
            template="Hello {{name}}",
            version="1.0",
            variables=["name"],
        )
        assert pt.name == "test_prompt"
        assert pt.template == "Hello {{name}}"
        assert pt.version == "1.0"
        assert pt.variables == ["name"]

    def test_create_with_default_variables(self) -> None:
        """variables should default to an empty list."""
        pt = PromptTemplate(
            name="simple",
            template="No variables here",
            version="0.1",
        )
        assert pt.variables == []

    def test_frozen_immutability(self) -> None:
        """PromptTemplate instances must be immutable."""
        pt = PromptTemplate(
            name="frozen",
            template="content",
            version="1.0",
        )
        with pytest.raises(AttributeError):
            pt.name = "changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# PromptTemplate validation
# ---------------------------------------------------------------------------


class TestPromptTemplateValidation:
    """Empty name or template must raise ValueError."""

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ValueError, match="name"):
            PromptTemplate(name="", template="valid", version="1.0")

    def test_empty_template_raises(self) -> None:
        with pytest.raises(ValueError, match="template"):
            PromptTemplate(name="valid", template="", version="1.0")

    def test_none_name_raises(self) -> None:
        """None should also be rejected as a name."""
        with pytest.raises((ValueError, TypeError)):
            PromptTemplate(name=None, template="valid", version="1.0")  # type: ignore[arg-type]

    def test_none_template_raises(self) -> None:
        """None should also be rejected as a template."""
        with pytest.raises((ValueError, TypeError)):
            PromptTemplate(name="valid", template=None, version="1.0")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# PromptTemplate.render()
# ---------------------------------------------------------------------------


class TestPromptTemplateRender:
    """render() substitutes {{variable}} placeholders with provided values."""

    def test_render_single_variable(self) -> None:
        pt = PromptTemplate(
            name="greeting",
            template="Hello {{name}}!",
            version="1.0",
            variables=["name"],
        )
        assert pt.render(name="World") == "Hello World!"

    def test_render_multiple_variables(self) -> None:
        pt = PromptTemplate(
            name="multi",
            template="{{greeting}}, {{name}}! You are {{age}} years old.",
            version="1.0",
            variables=["greeting", "name", "age"],
        )
        result = pt.render(greeting="Hi", name="Alice", age=30)
        assert result == "Hi, Alice! You are 30 years old."

    def test_render_converts_non_string_values(self) -> None:
        """Non-string kwargs should be converted via str()."""
        pt = PromptTemplate(
            name="number",
            template="Count: {{n}}",
            version="1.0",
            variables=["n"],
        )
        assert pt.render(n=42) == "Count: 42"

    def test_render_no_variables(self) -> None:
        """Template with no variables should return the template as-is."""
        pt = PromptTemplate(
            name="static",
            template="Static content",
            version="1.0",
            variables=[],
        )
        assert pt.render() == "Static content"

    def test_render_missing_variable_raises(self) -> None:
        pt = PromptTemplate(
            name="need_vars",
            template="{{a}} and {{b}}",
            version="1.0",
            variables=["a", "b"],
        )
        with pytest.raises(ValueError, match="Missing required variables"):
            pt.render(a="only_a")

    def test_render_all_missing_variables_raises(self) -> None:
        pt = PromptTemplate(
            name="need_vars",
            template="{{x}} {{y}}",
            version="1.0",
            variables=["x", "y"],
        )
        with pytest.raises(ValueError, match="Missing required variables"):
            pt.render()

    def test_render_extra_kwargs_ignored(self) -> None:
        """Extra keyword arguments beyond declared variables are silently ignored."""
        pt = PromptTemplate(
            name="extra",
            template="Hello {{name}}",
            version="1.0",
            variables=["name"],
        )
        result = pt.render(name="Bob", unused="value")
        assert result == "Hello Bob"

    def test_render_multiline_template(self) -> None:
        """Render should work correctly with multi-line templates."""
        pt = PromptTemplate(
            name="multiline",
            template="Line1: {{a}}\nLine2: {{b}}\n",
            version="1.0",
            variables=["a", "b"],
        )
        result = pt.render(a="foo", b="bar")
        assert result == "Line1: foo\nLine2: bar\n"


# ---------------------------------------------------------------------------
# PromptLoader — YAML loading
# ---------------------------------------------------------------------------


def _write_yaml(path: Path, data: dict | str) -> None:
    """Helper to write YAML content to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        if isinstance(data, str):
            f.write(data)
        else:
            yaml.dump(data, f, allow_unicode=True)


class TestPromptLoaderLoad:
    """PromptLoader.load() must read a YAML file and return a PromptTemplate."""

    def test_load_valid_yaml(self, tmp_path: Path) -> None:
        data = {
            "name": "entity_extraction",
            "version": "1.0",
            "variables": ["text", "language"],
            "template": "Extract entities from: {{text}} ({{language}})",
        }
        _write_yaml(tmp_path / "entity_extraction.yaml", data)
        loader = PromptLoader(prompts_dir=tmp_path)
        pt = loader.load(PromptType.ENTITY_EXTRACTION)

        assert pt.name == "entity_extraction"
        assert pt.version == "1.0"
        assert pt.variables == ["text", "language"]
        assert "{{text}}" in pt.template

    def test_load_returns_prompt_template_instance(self, tmp_path: Path) -> None:
        data = {
            "name": "search_query",
            "version": "1.0",
            "variables": ["query"],
            "template": "Search: {{query}}",
        }
        _write_yaml(tmp_path / "search_query.yaml", data)
        loader = PromptLoader(prompts_dir=tmp_path)
        pt = loader.load(PromptType.SEARCH_QUERY)
        assert isinstance(pt, PromptTemplate)

    def test_load_without_variables_defaults_to_empty(self, tmp_path: Path) -> None:
        data = {
            "name": "summarization",
            "version": "1.0",
            "template": "Summarize this text.",
        }
        _write_yaml(tmp_path / "summarization.yaml", data)
        loader = PromptLoader(prompts_dir=tmp_path)
        pt = loader.load(PromptType.SUMMARIZATION)
        assert pt.variables == []

    def test_load_file_not_found_raises(self, tmp_path: Path) -> None:
        loader = PromptLoader(prompts_dir=tmp_path)
        with pytest.raises(FileNotFoundError):
            loader.load(PromptType.ENTITY_EXTRACTION)

    def test_load_invalid_yaml_raises(self, tmp_path: Path) -> None:
        """Malformed YAML (non-dict top-level) should raise ValueError."""
        bad_yaml = "- this\n- is\n- a list\n"
        _write_yaml(tmp_path / "entity_extraction.yaml", bad_yaml)
        loader = PromptLoader(prompts_dir=tmp_path)
        with pytest.raises(ValueError, match="Invalid YAML"):
            loader.load(PromptType.ENTITY_EXTRACTION)

    def test_load_missing_name_raises(self, tmp_path: Path) -> None:
        data = {
            "version": "1.0",
            "template": "Hello",
        }
        _write_yaml(tmp_path / "entity_extraction.yaml", data)
        loader = PromptLoader(prompts_dir=tmp_path)
        with pytest.raises(ValueError, match="name"):
            loader.load(PromptType.ENTITY_EXTRACTION)

    def test_load_missing_template_raises(self, tmp_path: Path) -> None:
        data = {
            "name": "entity_extraction",
            "version": "1.0",
        }
        _write_yaml(tmp_path / "entity_extraction.yaml", data)
        loader = PromptLoader(prompts_dir=tmp_path)
        with pytest.raises(ValueError, match="template"):
            loader.load(PromptType.ENTITY_EXTRACTION)

    def test_load_missing_version_raises(self, tmp_path: Path) -> None:
        data = {
            "name": "entity_extraction",
            "template": "Hello",
        }
        _write_yaml(tmp_path / "entity_extraction.yaml", data)
        loader = PromptLoader(prompts_dir=tmp_path)
        with pytest.raises(ValueError, match="version"):
            loader.load(PromptType.ENTITY_EXTRACTION)

    def test_loaded_template_is_renderable(self, tmp_path: Path) -> None:
        """End-to-end: load from YAML, then render with variables."""
        data = {
            "name": "search_query",
            "version": "1.0",
            "variables": ["query", "context"],
            "template": "Query: {{query}}\nContext: {{context}}",
        }
        _write_yaml(tmp_path / "search_query.yaml", data)
        loader = PromptLoader(prompts_dir=tmp_path)
        pt = loader.load(PromptType.SEARCH_QUERY)
        result = pt.render(query="test question", context="some context")
        assert result == "Query: test question\nContext: some context"
