"""CompareRAGUseCase - VectorRAGとGraphRAGの並列検索・結果比較ユースケース"""

import asyncio
from dataclasses import dataclass, field

from src.application.interfaces import IEmbeddingService, ILLMService
from src.domain.models.query_result import QueryResult
from src.domain.repositories import IGraphRepository, IVectorRepository


@dataclass(frozen=True)
class ComparisonResult:
    """VectorRAGとGraphRAGの検索結果を集約した比較結果

    Attributes:
        query: 元のクエリ文字列
        vector_results: VectorRAGの検索結果リスト
        graph_results: GraphRAGの検索結果リスト
        vector_error: VectorRAG検索時のエラーメッセージ（エラーがなければNone）
        graph_error: GraphRAG検索時のエラーメッセージ（エラーがなければNone）
    """

    query: str
    vector_results: list[QueryResult] = field(default_factory=list)
    graph_results: list[QueryResult] = field(default_factory=list)
    vector_error: str | None = None
    graph_error: str | None = None


class CompareRAGUseCase:
    """VectorRAGとGraphRAGの並列検索・結果集約ユースケース

    Pipeline:
    1. IEmbeddingServiceでクエリの埋め込みベクトルを生成
    2. VectorRAG検索とGraphRAG検索をasyncio.gatherで並列実行
    3. 結果をComparisonResultに集約
    4. 個別の検索失敗をgracefulに処理
    """

    def __init__(
        self,
        vector_repo: IVectorRepository,
        graph_repo: IGraphRepository,
        llm_service: ILLMService,
        embedding_service: IEmbeddingService,
    ) -> None:
        self._vector_repo = vector_repo
        self._graph_repo = graph_repo
        self._llm_service = llm_service
        self._embedding_service = embedding_service

    async def execute(self, query: str, top_k: int = 5) -> ComparisonResult:
        """VectorRAGとGraphRAGの並列検索を実行し、比較結果を返す

        Args:
            query: 検索クエリ文字列
            top_k: VectorRAG検索で返す上位結果数（デフォルト: 5）

        Returns:
            ComparisonResult: 両方の検索結果を集約した比較結果
        """
        # Step 1: クエリの埋め込みベクトルを生成
        embeddings = await self._embedding_service.create_embeddings([query])
        query_embedding = embeddings[0]

        # Step 2: VectorRAG検索とGraphRAG検索を並列実行
        vector_results: list[QueryResult] = []
        graph_results: list[QueryResult] = []
        vector_error: str | None = None
        graph_error: str | None = None

        async def search_vector() -> None:
            nonlocal vector_results, vector_error
            try:
                vector_results = await self._vector_repo.search(query_embedding, top_k=top_k)
            except Exception as e:
                vector_error = str(e)

        async def search_graph() -> None:
            nonlocal graph_results, graph_error
            try:
                graph_results = await self._graph_repo.search(query)
            except Exception as e:
                graph_error = str(e)

        await asyncio.gather(search_vector(), search_graph())

        # Step 3: 結果をComparisonResultに集約
        return ComparisonResult(
            query=query,
            vector_results=vector_results,
            graph_results=graph_results,
            vector_error=vector_error,
            graph_error=graph_error,
        )
