"""Document entity - aggregate root for document processing lifecycle."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class DocumentStatus(Enum):
    """Possible states in the document processing lifecycle."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PARSED = "parsed"
    INDEXED = "indexed"
    FAILED = "failed"


class InvalidStateTransitionError(Exception):
    """Raised when an invalid document state transition is attempted."""

    pass


# Valid transitions map: from_status -> set of allowed to_statuses
_VALID_TRANSITIONS: dict[DocumentStatus, set[DocumentStatus]] = {
    DocumentStatus.UPLOADED: {DocumentStatus.PROCESSING, DocumentStatus.FAILED},
    DocumentStatus.PROCESSING: {DocumentStatus.PARSED, DocumentStatus.FAILED},
    DocumentStatus.PARSED: {DocumentStatus.INDEXED, DocumentStatus.FAILED},
    DocumentStatus.INDEXED: {DocumentStatus.FAILED},
    DocumentStatus.FAILED: set(),
}


@dataclass
class Document:
    """Document entity representing a file uploaded for RAG processing.

    This is a mutable entity (not frozen) because its state changes
    throughout the document processing lifecycle:
    UPLOADED -> PROCESSING -> PARSED -> INDEXED
    Any state can transition to FAILED.
    """

    filename: str
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: DocumentStatus = DocumentStatus.UPLOADED
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    parsed_content: str | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.filename:
            raise ValueError("Document filename cannot be empty")

    def _transition_to(self, new_status: DocumentStatus) -> None:
        """Validate and perform a state transition.

        Args:
            new_status: The target status to transition to.

        Raises:
            InvalidStateTransitionError: If the transition is not allowed.
        """
        if new_status not in _VALID_TRANSITIONS.get(self.status, set()):
            raise InvalidStateTransitionError(f"Cannot transition from {self.status.value} to {new_status.value}")
        self.status = new_status

    def start_processing(self) -> None:
        """Transition document status from UPLOADED to PROCESSING."""
        self._transition_to(DocumentStatus.PROCESSING)

    def mark_parsed(self, parsed_content: str) -> None:
        """Transition document status from PROCESSING to PARSED.

        Args:
            parsed_content: The extracted/parsed text content from the document.
        """
        self._transition_to(DocumentStatus.PARSED)
        self.parsed_content = parsed_content

    def mark_indexed(self) -> None:
        """Transition document status from PARSED to INDEXED."""
        self._transition_to(DocumentStatus.INDEXED)

    def mark_failed(self, error: str) -> None:
        """Transition document status to FAILED from any non-FAILED state.

        Args:
            error: Description of the error that caused the failure.

        Raises:
            InvalidStateTransitionError: If already in FAILED state.
        """
        if self.status == DocumentStatus.FAILED:
            raise InvalidStateTransitionError(f"Cannot transition from {self.status.value} to failed")
        self.status = DocumentStatus.FAILED
        self.error = error
