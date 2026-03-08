from abc import ABC, abstractmethod
from collections.abc import Callable

from src.domain.events import DomainEvent


class IEventDispatcher(ABC):
    """ドメインイベントのディスパッチを担当するインターフェース"""

    @abstractmethod
    async def dispatch(self, event: DomainEvent) -> None:
        """イベントを発行し、登録されたハンドラを実行する"""
        ...

    @abstractmethod
    def register(self, event_type: type[DomainEvent], handler: Callable) -> None:
        """イベントタイプに対するハンドラを登録する"""
        ...


class ILLMService(ABC):
    """LLM (Ollama) との通信を担当するサービスインターフェース"""

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """プロンプトを送信し、LLMからの応答を取得する"""
        ...


class IEmbeddingService(ABC):
    """埋め込みベクトル生成を担当するサービスインターフェース"""

    @abstractmethod
    async def create_embeddings(self, texts: list[str]) -> list[list[float]]:
        """テキストリストから埋め込みベクトルを生成する"""
        ...


class IFileParser(ABC):
    """ファイルからテキストを抽出するパーサーインターフェース"""

    @abstractmethod
    async def parse(self, file_path: str) -> str:
        """ファイルからテキストを抽出する"""
        ...
