"""Domain events for the Local RAG Comparator system."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events.

    Attributes:
        occurred_at: Timestamp when the event occurred. Auto-set to current time if not provided.
    """

    occurred_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(frozen=True)
class DocumentUploadedEvent(DomainEvent):
    """Event raised when a document is successfully uploaded.

    Attributes:
        document_id: The unique identifier of the uploaded document.
        filename: The original filename of the uploaded document.
        occurred_at: Inherited from DomainEvent.
    """

    document_id: str = ""
    filename: str = ""


@dataclass(frozen=True)
class FileDetectedEvent(DomainEvent):
    """Event raised when a new file is detected in the watched directory.

    Attributes:
        file_path: The full path to the detected file.
        filename: The name of the detected file.
        occurred_at: Inherited from DomainEvent.
    """

    file_path: str = ""
    filename: str = ""
