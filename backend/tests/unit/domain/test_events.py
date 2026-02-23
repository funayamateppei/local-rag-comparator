"""Tests for domain events."""

from datetime import datetime

import pytest

from src.domain.events import DomainEvent, DocumentUploadedEvent


class TestDomainEvent:
    """Tests for DomainEvent base class."""

    def test_domain_event_has_occurred_at(self):
        event = DomainEvent()

        assert isinstance(event.occurred_at, datetime)

    def test_domain_event_auto_sets_occurred_at(self):
        before = datetime.utcnow()
        event = DomainEvent()
        after = datetime.utcnow()

        assert before <= event.occurred_at <= after

    def test_domain_event_with_explicit_occurred_at(self):
        specific_time = datetime(2026, 6, 15, 10, 30, 0)
        event = DomainEvent(occurred_at=specific_time)

        assert event.occurred_at == specific_time

    def test_domain_event_is_immutable(self):
        event = DomainEvent()

        with pytest.raises(AttributeError):
            event.occurred_at = datetime(2026, 1, 1)


class TestDocumentUploadedEvent:
    """Tests for DocumentUploadedEvent."""

    def test_create_document_uploaded_event(self):
        event = DocumentUploadedEvent(
            document_id="doc-123",
            filename="report.pdf",
        )

        assert event.document_id == "doc-123"
        assert event.filename == "report.pdf"
        assert isinstance(event.occurred_at, datetime)

    def test_document_uploaded_event_auto_sets_occurred_at(self):
        before = datetime.utcnow()
        event = DocumentUploadedEvent(
            document_id="doc-456",
            filename="data.csv",
        )
        after = datetime.utcnow()

        assert before <= event.occurred_at <= after

    def test_document_uploaded_event_with_explicit_occurred_at(self):
        specific_time = datetime(2026, 3, 1, 8, 0, 0)
        event = DocumentUploadedEvent(
            document_id="doc-789",
            filename="notes.txt",
            occurred_at=specific_time,
        )

        assert event.occurred_at == specific_time

    def test_document_uploaded_event_is_immutable(self):
        event = DocumentUploadedEvent(
            document_id="doc-123",
            filename="report.pdf",
        )

        with pytest.raises(AttributeError):
            event.document_id = "modified"

        with pytest.raises(AttributeError):
            event.filename = "modified.pdf"

    def test_document_uploaded_event_inherits_from_domain_event(self):
        event = DocumentUploadedEvent(
            document_id="doc-123",
            filename="report.pdf",
        )

        assert isinstance(event, DomainEvent)
