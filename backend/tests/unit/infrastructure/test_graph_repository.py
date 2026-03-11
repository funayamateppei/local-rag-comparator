"""Tests for GraphRAGRepository infrastructure adapter.

TDD Red-Green: these tests verify that GraphRAGRepository correctly
implements IGraphRepository using Parquet-based storage and simple
entity/relationship search.
"""

from __future__ import annotations

import pytest

pd = pytest.importorskip("pandas", reason="pandas not installed")

import json
from pathlib import Path
import yaml
from src.domain.models.graph_data import Entity, GraphData, Relationship
from src.domain.models.query_result import QueryResult
from src.domain.repositories import IGraphRepository
from src.infrastructure.graph_repository import GraphRAGRepository

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def repo(tmp_path: Path) -> GraphRAGRepository:
    """Create a GraphRAGRepository backed by a temporary directory."""
    return GraphRAGRepository(data_dir=tmp_path)


@pytest.fixture
def sample_entities() -> tuple[Entity, ...]:
    return (
        Entity(name="Python", type="Language", description="A general-purpose programming language"),
        Entity(name="FastAPI", type="Framework", description="A modern web framework for Python"),
    )


@pytest.fixture
def sample_relationships() -> tuple[Relationship, ...]:
    return (
        Relationship(
            source="FastAPI",
            target="Python",
            relation_type="BUILT_WITH",
            description="FastAPI is built with Python",
        ),
    )


@pytest.fixture
def sample_graph_data(
    sample_entities: tuple[Entity, ...],
    sample_relationships: tuple[Relationship, ...],
) -> GraphData:
    return GraphData(entities=sample_entities, relationships=sample_relationships)


@pytest.fixture
def empty_graph_data() -> GraphData:
    return GraphData()


# ---------------------------------------------------------------------------
# Interface compliance
# ---------------------------------------------------------------------------


class TestGraphRAGRepositoryInterface:
    """GraphRAGRepository must implement IGraphRepository."""

    def test_is_instance_of_igraph_repository(self, repo: GraphRAGRepository) -> None:
        assert isinstance(repo, IGraphRepository)

    def test_has_store_graph_method(self, repo: GraphRAGRepository) -> None:
        assert callable(getattr(repo, "store_graph", None))

    def test_has_search_method(self, repo: GraphRAGRepository) -> None:
        assert callable(getattr(repo, "search", None))

    def test_has_get_graph_data_method(self, repo: GraphRAGRepository) -> None:
        assert callable(getattr(repo, "get_graph_data", None))


# ---------------------------------------------------------------------------
# store_graph
# ---------------------------------------------------------------------------


class TestGraphRAGRepositoryStoreGraph:
    """Tests for store_graph method."""

    @pytest.mark.asyncio
    async def test_creates_entities_parquet(
        self, repo: GraphRAGRepository, sample_graph_data: GraphData, tmp_path: Path
    ) -> None:
        """store_graph should create an entities.parquet file."""
        await repo.store_graph("doc1", sample_graph_data)

        entities_path = tmp_path / "doc1" / "entities.parquet"
        assert entities_path.exists()

    @pytest.mark.asyncio
    async def test_entities_parquet_has_correct_data(
        self, repo: GraphRAGRepository, sample_graph_data: GraphData, tmp_path: Path
    ) -> None:
        """entities.parquet should contain the correct entity rows."""
        await repo.store_graph("doc1", sample_graph_data)

        df = pd.read_parquet(tmp_path / "doc1" / "entities.parquet")
        assert len(df) == 2
        assert list(df.columns) == ["name", "type", "description"]
        assert df.iloc[0]["name"] == "Python"
        assert df.iloc[1]["name"] == "FastAPI"

    @pytest.mark.asyncio
    async def test_creates_relationships_parquet(
        self, repo: GraphRAGRepository, sample_graph_data: GraphData, tmp_path: Path
    ) -> None:
        """store_graph should create a relationships.parquet file."""
        await repo.store_graph("doc1", sample_graph_data)

        relationships_path = tmp_path / "doc1" / "relationships.parquet"
        assert relationships_path.exists()

    @pytest.mark.asyncio
    async def test_relationships_parquet_has_correct_data(
        self, repo: GraphRAGRepository, sample_graph_data: GraphData, tmp_path: Path
    ) -> None:
        """relationships.parquet should contain the correct relationship rows."""
        await repo.store_graph("doc1", sample_graph_data)

        df = pd.read_parquet(tmp_path / "doc1" / "relationships.parquet")
        assert len(df) == 1
        assert list(df.columns) == ["source", "target", "relation_type", "description"]
        assert df.iloc[0]["source"] == "FastAPI"
        assert df.iloc[0]["target"] == "Python"
        assert df.iloc[0]["relation_type"] == "BUILT_WITH"

    @pytest.mark.asyncio
    async def test_creates_metadata_json(
        self, repo: GraphRAGRepository, sample_graph_data: GraphData, tmp_path: Path
    ) -> None:
        """store_graph should create a metadata.json with document info."""
        await repo.store_graph("doc1", sample_graph_data)

        metadata_path = tmp_path / "doc1" / "metadata.json"
        assert metadata_path.exists()

        with open(metadata_path, encoding="utf-8") as f:
            metadata = json.load(f)

        assert metadata["document_id"] == "doc1"
        assert metadata["entity_count"] == 2
        assert metadata["relationship_count"] == 1

    @pytest.mark.asyncio
    async def test_empty_graph_data_creates_metadata_only(
        self, repo: GraphRAGRepository, empty_graph_data: GraphData, tmp_path: Path
    ) -> None:
        """store_graph with empty GraphData should create metadata but no parquet files."""
        await repo.store_graph("doc_empty", empty_graph_data)

        doc_dir = tmp_path / "doc_empty"
        assert (doc_dir / "metadata.json").exists()
        assert not (doc_dir / "entities.parquet").exists()
        assert not (doc_dir / "relationships.parquet").exists()

        with open(doc_dir / "metadata.json", encoding="utf-8") as f:
            metadata = json.load(f)
        assert metadata["entity_count"] == 0
        assert metadata["relationship_count"] == 0


# ---------------------------------------------------------------------------
# get_graph_data
# ---------------------------------------------------------------------------


class TestGraphRAGRepositoryGetGraphData:
    """Tests for get_graph_data method."""

    @pytest.mark.asyncio
    async def test_returns_correct_entities(self, repo: GraphRAGRepository, sample_graph_data: GraphData) -> None:
        """get_graph_data should return GraphData with the stored entities."""
        await repo.store_graph("doc1", sample_graph_data)

        result = await repo.get_graph_data("doc1")

        assert result is not None
        assert len(result.entities) == 2
        assert result.entities[0].name == "Python"
        assert result.entities[0].type == "Language"
        assert result.entities[1].name == "FastAPI"

    @pytest.mark.asyncio
    async def test_returns_correct_relationships(self, repo: GraphRAGRepository, sample_graph_data: GraphData) -> None:
        """get_graph_data should return GraphData with the stored relationships."""
        await repo.store_graph("doc1", sample_graph_data)

        result = await repo.get_graph_data("doc1")

        assert result is not None
        assert len(result.relationships) == 1
        assert result.relationships[0].source == "FastAPI"
        assert result.relationships[0].target == "Python"
        assert result.relationships[0].relation_type == "BUILT_WITH"

    @pytest.mark.asyncio
    async def test_returns_none_for_unknown_document(self, repo: GraphRAGRepository) -> None:
        """get_graph_data should return None when the document_id does not exist."""
        result = await repo.get_graph_data("nonexistent")
        assert result is None


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


class TestGraphRAGRepositorySearch:
    """Tests for search method."""

    @pytest.mark.asyncio
    async def test_finds_entity_by_name(self, repo: GraphRAGRepository, sample_graph_data: GraphData) -> None:
        """search should find entities whose name matches the query."""
        await repo.store_graph("doc1", sample_graph_data)

        results = await repo.search("Python")

        assert len(results) >= 1
        assert any("Python" in r.answer for r in results)

    @pytest.mark.asyncio
    async def test_finds_entity_by_description(self, repo: GraphRAGRepository, sample_graph_data: GraphData) -> None:
        """search should find entities whose description contains the query."""
        await repo.store_graph("doc1", sample_graph_data)

        results = await repo.search("modern web framework")

        assert len(results) >= 1
        assert any("FastAPI" in r.answer for r in results)

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_matches(
        self, repo: GraphRAGRepository, sample_graph_data: GraphData
    ) -> None:
        """search should return an empty list when no entities match."""
        await repo.store_graph("doc1", sample_graph_data)

        results = await repo.search("Haskell")

        assert results == []

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_data(self, repo: GraphRAGRepository) -> None:
        """search should return an empty list when no documents are stored."""
        results = await repo.search("anything")
        assert results == []

    @pytest.mark.asyncio
    async def test_results_are_query_result_instances(
        self, repo: GraphRAGRepository, sample_graph_data: GraphData
    ) -> None:
        """search results should be QueryResult instances with rag_type='graph'."""
        await repo.store_graph("doc1", sample_graph_data)

        results = await repo.search("Python")

        for r in results:
            assert isinstance(r, QueryResult)
            assert r.rag_type == "graph"
            assert r.query == "Python"

    @pytest.mark.asyncio
    async def test_results_sorted_by_score_descending(self, repo: GraphRAGRepository) -> None:
        """search results should be sorted by score in descending order."""
        # Create data where one entity matches by name (score=1.0) and another by description (score=0.7)
        graph_data = GraphData(
            entities=(
                Entity(name="Machine Learning", type="Concept", description="A branch of AI"),
                Entity(name="Neural Network", type="Concept", description="Used in machine learning systems"),
            ),
        )
        await repo.store_graph("doc1", graph_data)

        results = await repo.search("machine learning")

        assert len(results) == 2
        # Name match should come first (score=1.0), description match second (score=0.7)
        assert results[0].score >= results[1].score
        assert results[0].score == 1.0
        assert results[1].score == 0.7

    @pytest.mark.asyncio
    async def test_search_is_case_insensitive(self, repo: GraphRAGRepository, sample_graph_data: GraphData) -> None:
        """search should be case-insensitive."""
        await repo.store_graph("doc1", sample_graph_data)

        results = await repo.search("python")

        assert len(results) >= 1
        assert any("Python" in r.answer for r in results)

    @pytest.mark.asyncio
    async def test_search_includes_document_id_in_sources(
        self, repo: GraphRAGRepository, sample_graph_data: GraphData
    ) -> None:
        """search results should include the document_id in sources."""
        await repo.store_graph("doc1", sample_graph_data)

        results = await repo.search("Python")

        assert len(results) >= 1
        assert results[0].sources == ("doc1",)


# ---------------------------------------------------------------------------
# generate_settings_yaml
# ---------------------------------------------------------------------------


class TestGraphRAGRepositoryGenerateSettingsYaml:
    """Tests for generate_settings_yaml method."""

    def test_creates_settings_file(self, repo: GraphRAGRepository, tmp_path: Path) -> None:
        """generate_settings_yaml should create a settings.yaml file."""
        output_dir = tmp_path / "graphrag_output"
        output_dir.mkdir()

        settings_path = repo.generate_settings_yaml(output_dir)

        assert settings_path.exists()
        assert settings_path.name == "settings.yaml"

    def test_settings_contains_valid_yaml(self, repo: GraphRAGRepository, tmp_path: Path) -> None:
        """The generated file should be valid, parseable YAML."""
        output_dir = tmp_path / "graphrag_output"
        output_dir.mkdir()

        settings_path = repo.generate_settings_yaml(output_dir)

        with open(settings_path, encoding="utf-8") as f:
            settings = yaml.safe_load(f)
        assert isinstance(settings, dict)

    def test_settings_has_ollama_llm_config(self, tmp_path: Path) -> None:
        """The settings should point the LLM to Ollama."""
        repo = GraphRAGRepository(
            data_dir=tmp_path / "data",
            ollama_base_url="http://localhost:11434",
            llm_model="qwen2.5:14b",
        )
        output_dir = tmp_path / "graphrag_output"
        output_dir.mkdir()

        settings_path = repo.generate_settings_yaml(output_dir)

        with open(settings_path, encoding="utf-8") as f:
            settings = yaml.safe_load(f)

        assert settings["llm"]["api_base"] == "http://localhost:11434/v1"
        assert settings["llm"]["model"] == "qwen2.5:14b"
        assert settings["llm"]["type"] == "openai_chat"

    def test_settings_has_ollama_embedding_config(self, tmp_path: Path) -> None:
        """The settings should point embeddings to Ollama."""
        repo = GraphRAGRepository(
            data_dir=tmp_path / "data",
            ollama_base_url="http://localhost:11434",
            embedding_model="bge-m3",
        )
        output_dir = tmp_path / "graphrag_output"
        output_dir.mkdir()

        settings_path = repo.generate_settings_yaml(output_dir)

        with open(settings_path, encoding="utf-8") as f:
            settings = yaml.safe_load(f)

        assert settings["embeddings"]["llm"]["api_base"] == "http://localhost:11434/v1"
        assert settings["embeddings"]["llm"]["model"] == "bge-m3"
        assert settings["embeddings"]["llm"]["type"] == "openai_embedding"
