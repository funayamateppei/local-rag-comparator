"""Tests for InMemoryDocumentRepository infrastructure adapter.

TDD Red-Green: these tests verify that InMemoryDocumentRepository correctly
implements IDocumentRepository with in-memory storage.
"""

from __future__ import annotations

import pytest
from src.domain.models.document import Document
from src.domain.repositories import IDocumentRepository
from src.infrastructure.document_repository import InMemoryDocumentRepository


# ---------------------------------------------------------------------------
# Interface compliance
# ---------------------------------------------------------------------------


class TestInMemoryDocumentRepositoryInterface:
    """InMemoryDocumentRepository must implement IDocumentRepository."""

    def test_is_instance_of_idocument_repository(self) -> None:
        repo = InMemoryDocumentRepository()
        assert isinstance(repo, IDocumentRepository)

    def test_has_save_method(self) -> None:
        repo = InMemoryDocumentRepository()
        assert callable(getattr(repo, "save", None))

    def test_has_find_by_id_method(self) -> None:
        repo = InMemoryDocumentRepository()
        assert callable(getattr(repo, "find_by_id", None))

    def test_has_find_all_method(self) -> None:
        repo = InMemoryDocumentRepository()
        assert callable(getattr(repo, "find_all", None))


# ---------------------------------------------------------------------------
# save and find_by_id
# ---------------------------------------------------------------------------


class TestInMemoryDocumentRepositorySaveAndFind:
    """Tests for saving and retrieving documents."""

    async def test_save_and_find_by_id(self) -> None:
        repo = InMemoryDocumentRepository()
        doc = Document(id="doc-1", filename="test.pdf", content="Hello world")

        await repo.save(doc)
        result = await repo.find_by_id("doc-1")

        assert result is not None
        assert result.id == "doc-1"
        assert result.filename == "test.pdf"
        assert result.content == "Hello world"

    async def test_find_by_id_returns_none_for_missing_id(self) -> None:
        repo = InMemoryDocumentRepository()

        result = await repo.find_by_id("nonexistent-id")

        assert result is None

    async def test_save_overwrites_existing_document(self) -> None:
        repo = InMemoryDocumentRepository()
        doc_v1 = Document(id="doc-1", filename="v1.pdf", content="Version 1")
        doc_v2 = Document(id="doc-1", filename="v2.pdf", content="Version 2")

        await repo.save(doc_v1)
        await repo.save(doc_v2)
        result = await repo.find_by_id("doc-1")

        assert result is not None
        assert result.filename == "v2.pdf"
        assert result.content == "Version 2"


# ---------------------------------------------------------------------------
# find_all
# ---------------------------------------------------------------------------


class TestInMemoryDocumentRepositoryFindAll:
    """Tests for retrieving all documents."""

    async def test_find_all_returns_empty_list_when_no_documents(self) -> None:
        repo = InMemoryDocumentRepository()

        result = await repo.find_all()

        assert result == []

    async def test_find_all_returns_all_saved_documents(self) -> None:
        repo = InMemoryDocumentRepository()
        doc1 = Document(id="doc-1", filename="a.pdf", content="Content A")
        doc2 = Document(id="doc-2", filename="b.pdf", content="Content B")
        doc3 = Document(id="doc-3", filename="c.pdf", content="Content C")

        await repo.save(doc1)
        await repo.save(doc2)
        await repo.save(doc3)
        result = await repo.find_all()

        assert len(result) == 3
        ids = {d.id for d in result}
        assert ids == {"doc-1", "doc-2", "doc-3"}

    async def test_find_all_after_overwrite_does_not_duplicate(self) -> None:
        repo = InMemoryDocumentRepository()
        doc_v1 = Document(id="doc-1", filename="v1.pdf", content="Version 1")
        doc_v2 = Document(id="doc-1", filename="v2.pdf", content="Version 2")

        await repo.save(doc_v1)
        await repo.save(doc_v2)
        result = await repo.find_all()

        assert len(result) == 1
        assert result[0].filename == "v2.pdf"
