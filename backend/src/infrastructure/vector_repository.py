"""ChromaDB-based vector repository implementation."""

import chromadb

from src.domain.models.query_result import QueryResult
from src.domain.repositories import IVectorRepository


class ChromaDBVectorRepository(IVectorRepository):
    """IVectorRepository implementation using ChromaDB.

    Connects to ChromaDB server and manages document embeddings.
    """

    COLLECTION_NAME = "documents"

    def __init__(self, host: str = "localhost", port: int = 8001) -> None:
        self._client = chromadb.HttpClient(host=host, port=port)
        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    async def store_embeddings(self, document_id: str, chunks: list[str], embeddings: list[list[float]]) -> None:
        ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"document_id": document_id, "chunk_index": i} for i in range(len(chunks))]

        self._collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    async def search(self, query_embedding: list[float], top_k: int = 5) -> list[QueryResult]:
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "distances", "metadatas"],
        )

        query_results = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                distance = results["distances"][0][i] if results["distances"] else 0.0
                score = max(0.0, min(1.0, 1.0 - distance))
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                document_id = metadata.get("document_id", "unknown")

                query_results.append(
                    QueryResult(
                        query="",
                        answer=doc,
                        sources=(document_id,),
                        score=score,
                        rag_type="vector",
                    )
                )
        return query_results
