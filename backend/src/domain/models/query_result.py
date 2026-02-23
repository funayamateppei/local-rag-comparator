"""QueryResult value object - represents the result of a RAG query."""

from dataclasses import dataclass


@dataclass(frozen=True)
class QueryResult:
    """Immutable value object representing a RAG query result.

    Attributes:
        query: The original query string.
        answer: The generated answer.
        sources: Tuple of source document identifiers used to generate the answer.
        score: Confidence/relevance score between 0.0 and 1.0.
        rag_type: The RAG approach used - either "vector" or "graph".
    """

    query: str
    answer: str
    sources: tuple[str, ...]
    score: float
    rag_type: str  # "vector" or "graph"

    def __post_init__(self) -> None:
        if self.rag_type not in ("vector", "graph"):
            raise ValueError(
                f"rag_type must be 'vector' or 'graph', got '{self.rag_type}'"
            )
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(
                f"score must be between 0.0 and 1.0, got {self.score}"
            )
