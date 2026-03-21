"""Query router - handles vector and graph RAG search queries."""

from fastapi import APIRouter, Depends, HTTPException
from src.application.use_cases.compare_rag import CompareRAGUseCase
from src.interfaces.schemas import (
    ErrorResponse,
    GraphQueryResponse,
    QueryRequest,
    QueryResultResponse,
    VectorQueryResponse,
)

router = APIRouter(tags=["query"])


def get_compare_rag_use_case() -> CompareRAGUseCase:
    """DI placeholder - overridden in main.py"""
    raise NotImplementedError


@router.post(
    "/api/query/vector",
    response_model=VectorQueryResponse,
    responses={500: {"model": ErrorResponse}},
    summary="VectorRAGで検索する",
    description="ChromaDBのベクトル検索を使用してドキュメントを検索し、回答を生成する。",
)
async def vector_query(
    request: QueryRequest,
    use_case: CompareRAGUseCase = Depends(get_compare_rag_use_case),
) -> VectorQueryResponse:
    try:
        result = await use_case.execute(request.query, top_k=request.top_k)
        return VectorQueryResponse(
            query=request.query,
            results=[QueryResultResponse.from_domain(r) for r in result.vector_results],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/api/query/graph",
    response_model=GraphQueryResponse,
    responses={500: {"model": ErrorResponse}},
    summary="GraphRAGで検索する",
    description="ナレッジグラフを使用してドキュメントを検索し、回答を生成する。",
)
async def graph_query(
    request: QueryRequest,
    use_case: CompareRAGUseCase = Depends(get_compare_rag_use_case),
) -> GraphQueryResponse:
    try:
        result = await use_case.execute(request.query, top_k=request.top_k)
        return GraphQueryResponse(
            query=request.query,
            results=[QueryResultResponse.from_domain(r) for r in result.graph_results],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
