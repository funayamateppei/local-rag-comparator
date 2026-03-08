"""Tests for CompareRAGUseCase - parallel Vector/Graph RAG comparison."""

from unittest.mock import AsyncMock

import pytest
from src.application.use_cases.compare_rag import CompareRAGUseCase, ComparisonResult
from src.domain.models.query_result import QueryResult


@pytest.fixture
def mock_dependencies():
    return {
        "vector_repo": AsyncMock(),
        "graph_repo": AsyncMock(),
        "llm_service": AsyncMock(),
        "embedding_service": AsyncMock(),
    }


@pytest.fixture
def use_case(mock_dependencies):
    return CompareRAGUseCase(**mock_dependencies)


@pytest.fixture
def sample_vector_results():
    return [
        QueryResult(
            query="test query",
            answer="vector answer 1",
            sources=("doc1.pdf",),
            score=0.9,
            rag_type="vector",
        ),
        QueryResult(
            query="test query",
            answer="vector answer 2",
            sources=("doc2.pdf",),
            score=0.7,
            rag_type="vector",
        ),
    ]


@pytest.fixture
def sample_graph_results():
    return [
        QueryResult(
            query="test query",
            answer="graph answer 1",
            sources=("entity1",),
            score=0.85,
            rag_type="graph",
        ),
    ]


class TestCompareRAGUseCaseExecute:
    """Tests for CompareRAGUseCase.execute method."""

    @pytest.mark.asyncio
    async def test_execute_returns_comparison_result(self, use_case, mock_dependencies):
        """execute should return a ComparisonResult with vector_results, graph_results, and query."""
        mock_dependencies["embedding_service"].create_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_dependencies["vector_repo"].search.return_value = []
        mock_dependencies["graph_repo"].search.return_value = []

        result = await use_case.execute("test query")

        assert isinstance(result, ComparisonResult)
        assert hasattr(result, "vector_results")
        assert hasattr(result, "graph_results")
        assert hasattr(result, "query")

    @pytest.mark.asyncio
    async def test_execute_creates_query_embedding(self, use_case, mock_dependencies):
        """execute should call embedding_service.create_embeddings with the query text."""
        mock_dependencies["embedding_service"].create_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_dependencies["vector_repo"].search.return_value = []
        mock_dependencies["graph_repo"].search.return_value = []

        await use_case.execute("What is machine learning?")

        mock_dependencies["embedding_service"].create_embeddings.assert_called_once_with(["What is machine learning?"])

    @pytest.mark.asyncio
    async def test_execute_searches_vector_repo_with_embedding(self, use_case, mock_dependencies):
        """execute should call vector_repo.search with the generated embedding."""
        mock_dependencies["embedding_service"].create_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_dependencies["vector_repo"].search.return_value = []
        mock_dependencies["graph_repo"].search.return_value = []

        await use_case.execute("test query")

        mock_dependencies["vector_repo"].search.assert_called_once_with([0.1, 0.2, 0.3], top_k=5)

    @pytest.mark.asyncio
    async def test_execute_searches_graph_repo_with_query(self, use_case, mock_dependencies):
        """execute should call graph_repo.search with the original query string."""
        mock_dependencies["embedding_service"].create_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_dependencies["vector_repo"].search.return_value = []
        mock_dependencies["graph_repo"].search.return_value = []

        await use_case.execute("What is machine learning?")

        mock_dependencies["graph_repo"].search.assert_called_once_with("What is machine learning?")

    @pytest.mark.asyncio
    async def test_execute_parallel_search(self, use_case, mock_dependencies):
        """execute should initiate both vector and graph searches."""
        mock_dependencies["embedding_service"].create_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_dependencies["vector_repo"].search.return_value = []
        mock_dependencies["graph_repo"].search.return_value = []

        await use_case.execute("test query")

        # Both searches should have been called regardless of order
        assert mock_dependencies["vector_repo"].search.called
        assert mock_dependencies["graph_repo"].search.called

    @pytest.mark.asyncio
    async def test_execute_aggregates_vector_results(self, use_case, mock_dependencies, sample_vector_results):
        """ComparisonResult.vector_results should match what vector_repo.search returned."""
        mock_dependencies["embedding_service"].create_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_dependencies["vector_repo"].search.return_value = sample_vector_results
        mock_dependencies["graph_repo"].search.return_value = []

        result = await use_case.execute("test query")

        assert result.vector_results == sample_vector_results

    @pytest.mark.asyncio
    async def test_execute_aggregates_graph_results(self, use_case, mock_dependencies, sample_graph_results):
        """ComparisonResult.graph_results should match what graph_repo.search returned."""
        mock_dependencies["embedding_service"].create_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_dependencies["vector_repo"].search.return_value = []
        mock_dependencies["graph_repo"].search.return_value = sample_graph_results

        result = await use_case.execute("test query")

        assert result.graph_results == sample_graph_results

    @pytest.mark.asyncio
    async def test_execute_with_empty_vector_results(self, use_case, mock_dependencies):
        """When vector search returns empty list, ComparisonResult.vector_results should be empty."""
        mock_dependencies["embedding_service"].create_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_dependencies["vector_repo"].search.return_value = []
        mock_dependencies["graph_repo"].search.return_value = []

        result = await use_case.execute("test query")

        assert result.vector_results == []

    @pytest.mark.asyncio
    async def test_execute_with_empty_graph_results(self, use_case, mock_dependencies):
        """When graph search returns empty list, ComparisonResult.graph_results should be empty."""
        mock_dependencies["embedding_service"].create_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_dependencies["vector_repo"].search.return_value = []
        mock_dependencies["graph_repo"].search.return_value = []

        result = await use_case.execute("test query")

        assert result.graph_results == []

    @pytest.mark.asyncio
    async def test_execute_handles_vector_repo_error_gracefully(
        self, use_case, mock_dependencies, sample_graph_results
    ):
        """When vector_repo.search raises an exception, ComparisonResult should still contain graph results."""
        mock_dependencies["embedding_service"].create_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_dependencies["vector_repo"].search.side_effect = Exception("Vector DB connection failed")
        mock_dependencies["graph_repo"].search.return_value = sample_graph_results

        result = await use_case.execute("test query")

        assert result.vector_results == []
        assert result.vector_error == "Vector DB connection failed"
        assert result.graph_results == sample_graph_results
        assert result.graph_error is None

    @pytest.mark.asyncio
    async def test_execute_handles_graph_repo_error_gracefully(
        self, use_case, mock_dependencies, sample_vector_results
    ):
        """When graph_repo.search raises an exception, ComparisonResult should still contain vector results."""
        mock_dependencies["embedding_service"].create_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_dependencies["vector_repo"].search.return_value = sample_vector_results
        mock_dependencies["graph_repo"].search.side_effect = Exception("Graph DB connection failed")

        result = await use_case.execute("test query")

        assert result.graph_results == []
        assert result.graph_error == "Graph DB connection failed"
        assert result.vector_results == sample_vector_results
        assert result.vector_error is None

    @pytest.mark.asyncio
    async def test_execute_with_top_k_parameter(self, use_case, mock_dependencies):
        """top_k parameter should be passed to vector_repo.search."""
        mock_dependencies["embedding_service"].create_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_dependencies["vector_repo"].search.return_value = []
        mock_dependencies["graph_repo"].search.return_value = []

        await use_case.execute("test query", top_k=10)

        mock_dependencies["vector_repo"].search.assert_called_once_with([0.1, 0.2, 0.3], top_k=10)

    @pytest.mark.asyncio
    async def test_comparison_result_has_correct_query(self, use_case, mock_dependencies):
        """ComparisonResult.query should match the input query."""
        mock_dependencies["embedding_service"].create_embeddings.return_value = [[0.1, 0.2, 0.3]]
        mock_dependencies["vector_repo"].search.return_value = []
        mock_dependencies["graph_repo"].search.return_value = []

        result = await use_case.execute("What is deep learning?")

        assert result.query == "What is deep learning?"
