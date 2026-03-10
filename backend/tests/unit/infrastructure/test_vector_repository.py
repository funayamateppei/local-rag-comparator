"""Tests for ChromaDBVectorRepository infrastructure adapter.

TDD Red-Green: these tests verify that ChromaDBVectorRepository correctly
implements IVectorRepository using a mocked ChromaDB client.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from src.domain.models.query_result import QueryResult
from src.domain.repositories import IVectorRepository
from src.infrastructure.vector_repository import ChromaDBVectorRepository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_collection() -> MagicMock:
    """Create a mock ChromaDB collection."""
    return MagicMock()


@pytest.fixture
def mock_client(mock_collection: MagicMock) -> MagicMock:
    """Create a mock ChromaDB HttpClient that returns the mock collection."""
    client = MagicMock()
    client.get_or_create_collection.return_value = mock_collection
    return client


@pytest.fixture
def repo(mock_client: MagicMock) -> ChromaDBVectorRepository:
    """Create a ChromaDBVectorRepository with a mocked client."""
    with patch("src.infrastructure.vector_repository.chromadb.HttpClient", return_value=mock_client):
        return ChromaDBVectorRepository(host="localhost", port=8001)


# ---------------------------------------------------------------------------
# Interface compliance
# ---------------------------------------------------------------------------


class TestChromaDBVectorRepositoryInterface:
    """ChromaDBVectorRepository must implement IVectorRepository."""

    def test_is_instance_of_ivector_repository(self, repo: ChromaDBVectorRepository) -> None:
        assert isinstance(repo, IVectorRepository)

    def test_has_store_embeddings_method(self, repo: ChromaDBVectorRepository) -> None:
        assert callable(getattr(repo, "store_embeddings", None))

    def test_has_search_method(self, repo: ChromaDBVectorRepository) -> None:
        assert callable(getattr(repo, "search", None))


# ---------------------------------------------------------------------------
# store_embeddings
# ---------------------------------------------------------------------------


class TestChromaDBVectorRepositoryStoreEmbeddings:
    """Tests for storing embeddings in ChromaDB."""

    async def test_store_embeddings_creates_correct_ids(
        self, repo: ChromaDBVectorRepository, mock_collection: MagicMock
    ) -> None:
        chunks = ["chunk 0", "chunk 1", "chunk 2"]
        embeddings = [[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]

        await repo.store_embeddings("doc-1", chunks, embeddings)

        mock_collection.add.assert_called_once()
        call_kwargs = mock_collection.add.call_args[1]
        assert call_kwargs["ids"] == ["doc-1_chunk_0", "doc-1_chunk_1", "doc-1_chunk_2"]

    async def test_store_embeddings_passes_documents(
        self, repo: ChromaDBVectorRepository, mock_collection: MagicMock
    ) -> None:
        chunks = ["chunk A", "chunk B"]
        embeddings = [[0.1], [0.2]]

        await repo.store_embeddings("doc-2", chunks, embeddings)

        call_kwargs = mock_collection.add.call_args[1]
        assert call_kwargs["documents"] == ["chunk A", "chunk B"]

    async def test_store_embeddings_passes_embeddings(
        self, repo: ChromaDBVectorRepository, mock_collection: MagicMock
    ) -> None:
        chunks = ["chunk A"]
        embeddings = [[0.1, 0.2, 0.3]]

        await repo.store_embeddings("doc-3", chunks, embeddings)

        call_kwargs = mock_collection.add.call_args[1]
        assert call_kwargs["embeddings"] == [[0.1, 0.2, 0.3]]

    async def test_store_embeddings_creates_correct_metadata(
        self, repo: ChromaDBVectorRepository, mock_collection: MagicMock
    ) -> None:
        chunks = ["chunk 0", "chunk 1"]
        embeddings = [[0.1], [0.2]]

        await repo.store_embeddings("doc-4", chunks, embeddings)

        call_kwargs = mock_collection.add.call_args[1]
        assert call_kwargs["metadatas"] == [
            {"document_id": "doc-4", "chunk_index": 0},
            {"document_id": "doc-4", "chunk_index": 1},
        ]


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------


class TestChromaDBVectorRepositorySearch:
    """Tests for searching embeddings in ChromaDB."""

    async def test_search_returns_query_result_objects(
        self, repo: ChromaDBVectorRepository, mock_collection: MagicMock
    ) -> None:
        mock_collection.query.return_value = {
            "documents": [["Result text"]],
            "distances": [[0.2]],
            "metadatas": [[{"document_id": "doc-1", "chunk_index": 0}]],
        }

        results = await repo.search([0.1, 0.2, 0.3], top_k=1)

        assert len(results) == 1
        assert isinstance(results[0], QueryResult)

    async def test_search_result_has_vector_rag_type(
        self, repo: ChromaDBVectorRepository, mock_collection: MagicMock
    ) -> None:
        mock_collection.query.return_value = {
            "documents": [["Some answer"]],
            "distances": [[0.1]],
            "metadatas": [[{"document_id": "doc-1", "chunk_index": 0}]],
        }

        results = await repo.search([0.1], top_k=1)

        assert results[0].rag_type == "vector"

    async def test_search_result_contains_document_text_as_answer(
        self, repo: ChromaDBVectorRepository, mock_collection: MagicMock
    ) -> None:
        mock_collection.query.return_value = {
            "documents": [["The quick brown fox"]],
            "distances": [[0.0]],
            "metadatas": [[{"document_id": "doc-1", "chunk_index": 0}]],
        }

        results = await repo.search([0.5], top_k=1)

        assert results[0].answer == "The quick brown fox"

    async def test_search_result_contains_document_id_in_sources(
        self, repo: ChromaDBVectorRepository, mock_collection: MagicMock
    ) -> None:
        mock_collection.query.return_value = {
            "documents": [["text"]],
            "distances": [[0.3]],
            "metadatas": [[{"document_id": "doc-42", "chunk_index": 0}]],
        }

        results = await repo.search([0.1], top_k=1)

        assert results[0].sources == ("doc-42",)

    async def test_search_with_empty_results(
        self, repo: ChromaDBVectorRepository, mock_collection: MagicMock
    ) -> None:
        mock_collection.query.return_value = {
            "documents": [[]],
            "distances": [[]],
            "metadatas": [[]],
        }

        results = await repo.search([0.1, 0.2], top_k=5)

        assert results == []

    async def test_search_with_none_documents(
        self, repo: ChromaDBVectorRepository, mock_collection: MagicMock
    ) -> None:
        mock_collection.query.return_value = {
            "documents": None,
            "distances": None,
            "metadatas": None,
        }

        results = await repo.search([0.1], top_k=3)

        assert results == []

    async def test_search_score_calculation_zero_distance(
        self, repo: ChromaDBVectorRepository, mock_collection: MagicMock
    ) -> None:
        """Distance 0.0 should yield score 1.0 (perfect match)."""
        mock_collection.query.return_value = {
            "documents": [["perfect match"]],
            "distances": [[0.0]],
            "metadatas": [[{"document_id": "doc-1", "chunk_index": 0}]],
        }

        results = await repo.search([0.1], top_k=1)

        assert results[0].score == 1.0

    async def test_search_score_calculation_full_distance(
        self, repo: ChromaDBVectorRepository, mock_collection: MagicMock
    ) -> None:
        """Distance 1.0 should yield score 0.0."""
        mock_collection.query.return_value = {
            "documents": [["no match"]],
            "distances": [[1.0]],
            "metadatas": [[{"document_id": "doc-1", "chunk_index": 0}]],
        }

        results = await repo.search([0.1], top_k=1)

        assert results[0].score == 0.0

    async def test_search_score_clamped_for_negative_result(
        self, repo: ChromaDBVectorRepository, mock_collection: MagicMock
    ) -> None:
        """Distance > 1.0 should yield score clamped to 0.0."""
        mock_collection.query.return_value = {
            "documents": [["far away"]],
            "distances": [[1.5]],
            "metadatas": [[{"document_id": "doc-1", "chunk_index": 0}]],
        }

        results = await repo.search([0.1], top_k=1)

        assert results[0].score == 0.0

    async def test_search_multiple_results(
        self, repo: ChromaDBVectorRepository, mock_collection: MagicMock
    ) -> None:
        mock_collection.query.return_value = {
            "documents": [["first", "second", "third"]],
            "distances": [[0.1, 0.3, 0.5]],
            "metadatas": [
                [
                    {"document_id": "doc-a", "chunk_index": 0},
                    {"document_id": "doc-b", "chunk_index": 1},
                    {"document_id": "doc-c", "chunk_index": 2},
                ]
            ],
        }

        results = await repo.search([0.1, 0.2], top_k=3)

        assert len(results) == 3
        assert results[0].answer == "first"
        assert results[1].answer == "second"
        assert results[2].answer == "third"
        assert results[0].score == pytest.approx(0.9)
        assert results[1].score == pytest.approx(0.7)
        assert results[2].score == pytest.approx(0.5)

    async def test_search_passes_correct_parameters_to_collection(
        self, repo: ChromaDBVectorRepository, mock_collection: MagicMock
    ) -> None:
        mock_collection.query.return_value = {
            "documents": [[]],
            "distances": [[]],
            "metadatas": [[]],
        }

        await repo.search([0.1, 0.2], top_k=10)

        mock_collection.query.assert_called_once_with(
            query_embeddings=[[0.1, 0.2]],
            n_results=10,
            include=["documents", "distances", "metadatas"],
        )
