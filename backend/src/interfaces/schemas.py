"""Pydantic Request/Response schemas for the API interface layer."""

from pydantic import BaseModel, Field
from src.domain.models.document import Document
from src.domain.models.query_result import QueryResult


class UploadResponse(BaseModel):
    """ファイルアップロードのレスポンススキーマ"""

    document_id: str = Field(..., description="アップロードされたドキュメントのID")
    filename: str = Field(..., description="アップロードされたファイル名")
    status: str = Field(..., description="ドキュメントの処理ステータス")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "document_id": "550e8400-e29b-41d4-a716-446655440000",
                    "filename": "document.pdf",
                    "status": "indexed",
                }
            ]
        }
    }

    @classmethod
    def from_domain(cls, document: Document) -> "UploadResponse":
        """ドメインモデルからレスポンススキーマに変換する"""
        return cls(
            document_id=document.id,
            filename=document.filename,
            status=document.status.value,
        )


class QueryRequest(BaseModel):
    """RAG検索リクエストスキーマ"""

    query: str = Field(..., min_length=1, description="検索クエリ文字列")
    top_k: int = Field(default=5, ge=1, le=100, description="返却する上位結果数")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "走れメロスの主人公は誰ですか？",
                    "top_k": 5,
                }
            ]
        }
    }


class QueryResultResponse(BaseModel):
    """個別のRAG検索結果スキーマ"""

    query: str = Field(..., description="元のクエリ文字列")
    answer: str = Field(..., description="生成された回答テキスト")
    sources: list[str] = Field(..., description="回答生成に使用されたソースドキュメントID")
    score: float = Field(..., ge=0.0, le=1.0, description="信頼度スコア (0.0〜1.0)")
    rag_type: str = Field(..., description="使用されたRAGタイプ (vector or graph)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "走れメロスの主人公は誰ですか？",
                    "answer": "走れメロスの主人公はメロスです。",
                    "sources": ["doc-001"],
                    "score": 0.95,
                    "rag_type": "vector",
                }
            ]
        }
    }

    @classmethod
    def from_domain(cls, result: QueryResult) -> "QueryResultResponse":
        """ドメインモデルからレスポンススキーマに変換する"""
        return cls(
            query=result.query,
            answer=result.answer,
            sources=list(result.sources),
            score=result.score,
            rag_type=result.rag_type,
        )


class VectorQueryResponse(BaseModel):
    """VectorRAG検索レスポンススキーマ"""

    query: str = Field(..., description="元のクエリ文字列")
    results: list[QueryResultResponse] = Field(..., description="検索結果リスト")


class GraphQueryResponse(BaseModel):
    """GraphRAG検索レスポンススキーマ"""

    query: str = Field(..., description="元のクエリ文字列")
    results: list[QueryResultResponse] = Field(..., description="検索結果リスト")


class ErrorResponse(BaseModel):
    """エラーレスポンススキーマ"""

    detail: str = Field(..., description="エラーの詳細メッセージ")
