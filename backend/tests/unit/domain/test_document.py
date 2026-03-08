"""Tests for Document entity domain model."""

from datetime import datetime

import pytest
from src.domain.models.document import (
    Document,
    DocumentStatus,
    InvalidStateTransitionError,
)


class TestDocumentCreation:
    """Tests for Document entity creation."""

    def test_create_document_with_required_fields(self):
        doc = Document(filename="test.pdf", content="Some content")

        assert doc.filename == "test.pdf"
        assert doc.content == "Some content"
        assert doc.status == DocumentStatus.UPLOADED
        assert isinstance(doc.id, str)
        assert len(doc.id) > 0
        assert isinstance(doc.created_at, datetime)
        assert doc.metadata == {}
        assert doc.parsed_content is None
        assert doc.error is None

    def test_create_document_with_all_fields(self):
        now = datetime(2026, 1, 1, 12, 0, 0)
        doc = Document(
            id="custom-id",
            filename="report.pdf",
            content="Full content here",
            status=DocumentStatus.UPLOADED,
            metadata={"author": "Alice"},
            created_at=now,
        )

        assert doc.id == "custom-id"
        assert doc.filename == "report.pdf"
        assert doc.content == "Full content here"
        assert doc.status == DocumentStatus.UPLOADED
        assert doc.metadata == {"author": "Alice"}
        assert doc.created_at == now

    def test_create_document_generates_unique_ids(self):
        doc1 = Document(filename="a.pdf", content="a")
        doc2 = Document(filename="b.pdf", content="b")

        assert doc1.id != doc2.id

    def test_create_document_with_empty_filename_raises_value_error(self):
        with pytest.raises(ValueError, match="filename cannot be empty"):
            Document(filename="", content="content")

    def test_create_document_default_status_is_uploaded(self):
        doc = Document(filename="test.pdf", content="content")
        assert doc.status == DocumentStatus.UPLOADED


class TestDocumentStateTransitions:
    """Tests for Document state machine transitions."""

    def test_start_processing_from_uploaded(self):
        doc = Document(filename="test.pdf", content="content")
        assert doc.status == DocumentStatus.UPLOADED

        doc.start_processing()

        assert doc.status == DocumentStatus.PROCESSING

    def test_mark_parsed_from_processing(self):
        doc = Document(filename="test.pdf", content="content")
        doc.start_processing()

        doc.mark_parsed("Parsed text content")

        assert doc.status == DocumentStatus.PARSED
        assert doc.parsed_content == "Parsed text content"

    def test_mark_indexed_from_parsed(self):
        doc = Document(filename="test.pdf", content="content")
        doc.start_processing()
        doc.mark_parsed("parsed")

        doc.mark_indexed()

        assert doc.status == DocumentStatus.INDEXED

    def test_mark_failed_from_uploaded(self):
        doc = Document(filename="test.pdf", content="content")

        doc.mark_failed("Upload validation error")

        assert doc.status == DocumentStatus.FAILED
        assert doc.error == "Upload validation error"

    def test_mark_failed_from_processing(self):
        doc = Document(filename="test.pdf", content="content")
        doc.start_processing()

        doc.mark_failed("Processing error")

        assert doc.status == DocumentStatus.FAILED
        assert doc.error == "Processing error"

    def test_mark_failed_from_parsed(self):
        doc = Document(filename="test.pdf", content="content")
        doc.start_processing()
        doc.mark_parsed("parsed")

        doc.mark_failed("Indexing error")

        assert doc.status == DocumentStatus.FAILED
        assert doc.error == "Indexing error"

    def test_mark_failed_from_indexed(self):
        doc = Document(filename="test.pdf", content="content")
        doc.start_processing()
        doc.mark_parsed("parsed")
        doc.mark_indexed()

        doc.mark_failed("Post-index error")

        assert doc.status == DocumentStatus.FAILED
        assert doc.error == "Post-index error"


class TestDocumentInvalidTransitions:
    """Tests for invalid state transitions that should raise errors."""

    def test_cannot_transition_from_uploaded_to_indexed(self):
        doc = Document(filename="test.pdf", content="content")

        with pytest.raises(InvalidStateTransitionError):
            doc.mark_indexed()

    def test_cannot_transition_from_uploaded_to_parsed(self):
        doc = Document(filename="test.pdf", content="content")

        with pytest.raises(InvalidStateTransitionError):
            doc.mark_parsed("parsed")

    def test_cannot_transition_from_processing_to_indexed(self):
        doc = Document(filename="test.pdf", content="content")
        doc.start_processing()

        with pytest.raises(InvalidStateTransitionError):
            doc.mark_indexed()

    def test_cannot_start_processing_from_parsed(self):
        doc = Document(filename="test.pdf", content="content")
        doc.start_processing()
        doc.mark_parsed("parsed")

        with pytest.raises(InvalidStateTransitionError):
            doc.start_processing()

    def test_cannot_start_processing_from_indexed(self):
        doc = Document(filename="test.pdf", content="content")
        doc.start_processing()
        doc.mark_parsed("parsed")
        doc.mark_indexed()

        with pytest.raises(InvalidStateTransitionError):
            doc.start_processing()

    def test_cannot_transition_from_failed(self):
        doc = Document(filename="test.pdf", content="content")
        doc.mark_failed("error")

        with pytest.raises(InvalidStateTransitionError):
            doc.start_processing()

    def test_cannot_mark_failed_from_failed(self):
        doc = Document(filename="test.pdf", content="content")
        doc.mark_failed("first error")

        with pytest.raises(InvalidStateTransitionError):
            doc.mark_failed("second error")
