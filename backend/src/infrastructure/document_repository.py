"""In-memory document repository implementation."""

from src.domain.models.document import Document
from src.domain.repositories import IDocumentRepository


class InMemoryDocumentRepository(IDocumentRepository):
    """Simple in-memory IDocumentRepository for development and testing."""

    def __init__(self) -> None:
        self._documents: dict[str, Document] = {}

    async def save(self, document: Document) -> None:
        self._documents[document.id] = document

    async def find_by_id(self, document_id: str) -> Document | None:
        return self._documents.get(document_id)

    async def find_all(self) -> list[Document]:
        return list(self._documents.values())
