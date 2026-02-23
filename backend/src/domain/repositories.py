from abc import ABC, abstractmethod
from typing import Optional

from src.domain.models.document import Document
from src.domain.models.query_result import QueryResult
from src.domain.models.graph_data import GraphData
from src.domain.models.prompt import PromptTemplate, PromptType


class IDocumentRepository(ABC):
    """ドキュメントの永続化を担当するリポジトリインターフェース"""

    @abstractmethod
    async def save(self, document: Document) -> None:
        """ドキュメントを保存する"""
        ...

    @abstractmethod
    async def find_by_id(self, document_id: str) -> Optional[Document]:
        """IDでドキュメントを検索する"""
        ...

    @abstractmethod
    async def find_all(self) -> list[Document]:
        """全ドキュメントを取得する"""
        ...


class IVectorRepository(ABC):
    """ベクトルDB (ChromaDB) とのやり取りを担当するリポジトリインターフェース"""

    @abstractmethod
    async def store_embeddings(
        self, document_id: str, chunks: list[str], embeddings: list[list[float]]
    ) -> None:
        """テキストチャンクとその埋め込みベクトルを保存する"""
        ...

    @abstractmethod
    async def search(
        self, query_embedding: list[float], top_k: int = 5
    ) -> list[QueryResult]:
        """クエリの埋め込みベクトルで類似検索を実行する"""
        ...


class IGraphRepository(ABC):
    """Knowledge Graph (GraphRAG) とのやり取りを担当するリポジトリインターフェース"""

    @abstractmethod
    async def store_graph(self, document_id: str, graph_data: GraphData) -> None:
        """グラフデータを保存する"""
        ...

    @abstractmethod
    async def search(self, query: str) -> list[QueryResult]:
        """グラフベースの検索を実行する"""
        ...

    @abstractmethod
    async def get_graph_data(self, document_id: str) -> Optional[GraphData]:
        """ドキュメントIDに紐づくグラフデータを取得する"""
        ...


class IPromptRepository(ABC):
    """プロンプトテンプレートの読み込みを担当するリポジトリインターフェース"""

    @abstractmethod
    def load(self, prompt_type: PromptType) -> PromptTemplate:
        """指定タイプのプロンプトテンプレートを読み込む"""
        ...
