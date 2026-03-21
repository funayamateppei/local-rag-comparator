from fastapi import FastAPI
from src.application.event_dispatcher import EventDispatcher
from src.application.use_cases.compare_rag import CompareRAGUseCase
from src.application.use_cases.document_processor import DocumentProcessorUseCase
from src.infrastructure.document_repository import InMemoryDocumentRepository
from src.infrastructure.file_parser import PyMuPDFFileParser
from src.infrastructure.graph_repository import GraphRAGRepository
from src.infrastructure.ollama_service import OllamaEmbeddingService, OllamaLLMService
from src.infrastructure.prompt_repository import PromptRepository
from src.infrastructure.vector_repository import ChromaDBVectorRepository
from src.interfaces.routers.query import get_compare_rag_use_case
from src.interfaces.routers.query import router as query_router
from src.interfaces.routers.upload import get_document_processor_use_case
from src.interfaces.routers.upload import router as upload_router

app = FastAPI(
    title="Local RAG Comparator API",
    description="Vector RAG vs GraphRAG 比較検証 API",
    version="0.1.0",
    openapi_tags=[
        {"name": "health", "description": "ヘルスチェック"},
        {"name": "upload", "description": "ドキュメントアップロード・処理"},
        {"name": "query", "description": "RAG検索クエリ"},
    ],
)

# Infrastructure instances
document_repo = InMemoryDocumentRepository()
vector_repo = ChromaDBVectorRepository()
graph_repo = GraphRAGRepository()
llm_service = OllamaLLMService()
embedding_service = OllamaEmbeddingService()
prompt_repo = PromptRepository()
file_parser = PyMuPDFFileParser()
event_dispatcher = EventDispatcher()

# Use case instances
document_processor_use_case = DocumentProcessorUseCase(
    document_repo=document_repo,
    prompt_repo=prompt_repo,
    vector_repo=vector_repo,
    graph_repo=graph_repo,
    event_dispatcher=event_dispatcher,
    llm_service=llm_service,
    embedding_service=embedding_service,
    file_parser=file_parser,
)

compare_rag_use_case = CompareRAGUseCase(
    vector_repo=vector_repo,
    graph_repo=graph_repo,
    llm_service=llm_service,
    embedding_service=embedding_service,
)


# DI overrides
def _get_document_processor_use_case() -> DocumentProcessorUseCase:
    return document_processor_use_case


def _get_compare_rag_use_case() -> CompareRAGUseCase:
    return compare_rag_use_case


app.dependency_overrides[get_document_processor_use_case] = _get_document_processor_use_case
app.dependency_overrides[get_compare_rag_use_case] = _get_compare_rag_use_case

# Router registration
app.include_router(upload_router)
app.include_router(query_router)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
