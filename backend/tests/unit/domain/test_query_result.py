"""Tests for QueryResult value object."""

import pytest
from src.domain.models.query_result import QueryResult


class TestQueryResultCreation:
    """Tests for QueryResult value object creation."""

    def test_create_query_result_with_vector_rag_type(self):
        result = QueryResult(
            query="What is RAG?",
            answer="RAG stands for Retrieval Augmented Generation.",
            sources=("doc1.pdf", "doc2.pdf"),
            score=0.85,
            rag_type="vector",
        )

        assert result.query == "What is RAG?"
        assert result.answer == "RAG stands for Retrieval Augmented Generation."
        assert result.sources == ("doc1.pdf", "doc2.pdf")
        assert result.score == 0.85
        assert result.rag_type == "vector"

    def test_create_query_result_with_graph_rag_type(self):
        result = QueryResult(
            query="Explain knowledge graphs.",
            answer="Knowledge graphs represent entities and relationships.",
            sources=("paper1.pdf",),
            score=0.92,
            rag_type="graph",
        )

        assert result.rag_type == "graph"
        assert result.score == 0.92

    def test_create_query_result_with_empty_sources(self):
        result = QueryResult(
            query="test",
            answer="answer",
            sources=(),
            score=0.5,
            rag_type="vector",
        )

        assert result.sources == ()

    def test_create_query_result_with_boundary_score_zero(self):
        result = QueryResult(
            query="test",
            answer="answer",
            sources=(),
            score=0.0,
            rag_type="vector",
        )

        assert result.score == 0.0

    def test_create_query_result_with_boundary_score_one(self):
        result = QueryResult(
            query="test",
            answer="answer",
            sources=(),
            score=1.0,
            rag_type="graph",
        )

        assert result.score == 1.0


class TestQueryResultValidation:
    """Tests for QueryResult validation."""

    def test_invalid_rag_type_raises_value_error(self):
        with pytest.raises(ValueError, match="rag_type must be 'vector' or 'graph'"):
            QueryResult(
                query="test",
                answer="answer",
                sources=(),
                score=0.5,
                rag_type="hybrid",
            )

    def test_empty_rag_type_raises_value_error(self):
        with pytest.raises(ValueError, match="rag_type must be 'vector' or 'graph'"):
            QueryResult(
                query="test",
                answer="answer",
                sources=(),
                score=0.5,
                rag_type="",
            )

    def test_score_below_zero_raises_value_error(self):
        with pytest.raises(ValueError, match="score must be between 0.0 and 1.0"):
            QueryResult(
                query="test",
                answer="answer",
                sources=(),
                score=-0.1,
                rag_type="vector",
            )

    def test_score_above_one_raises_value_error(self):
        with pytest.raises(ValueError, match="score must be between 0.0 and 1.0"):
            QueryResult(
                query="test",
                answer="answer",
                sources=(),
                score=1.1,
                rag_type="vector",
            )


class TestQueryResultImmutability:
    """Tests for QueryResult immutability (frozen dataclass)."""

    def test_query_result_is_immutable(self):
        result = QueryResult(
            query="test",
            answer="answer",
            sources=("doc.pdf",),
            score=0.5,
            rag_type="vector",
        )

        with pytest.raises(AttributeError):
            result.query = "modified"

        with pytest.raises(AttributeError):
            result.score = 0.9

        with pytest.raises(AttributeError):
            result.rag_type = "graph"
