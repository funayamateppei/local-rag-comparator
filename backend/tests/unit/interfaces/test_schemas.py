"""Tests for Pydantic Request/Response schemas."""

import pytest
from pydantic import ValidationError
from src.domain.models.document import Document
from src.domain.models.query_result import QueryResult
from src.interfaces.schemas import (
    ErrorResponse,
    GraphQueryResponse,
    QueryRequest,
    QueryResultResponse,
    UploadResponse,
    VectorQueryResponse,
)


class TestUploadResponse:
    def test_create_upload_response(self):
        response = UploadResponse(
            document_id="test-id",
            filename="test.pdf",
            status="indexed",
        )
        assert response.document_id == "test-id"
        assert response.filename == "test.pdf"
        assert response.status == "indexed"

    def test_from_domain(self):
        document = Document(filename="test.pdf", content="some content")
        document.start_processing()
        document.mark_parsed("parsed")
        document.mark_indexed()

        response = UploadResponse.from_domain(document)
        assert response.document_id == document.id
        assert response.filename == "test.pdf"
        assert response.status == "indexed"

    def test_from_domain_failed_status(self):
        document = Document(filename="error.pdf", content="content")
        document.mark_failed("parse error")

        response = UploadResponse.from_domain(document)
        assert response.status == "failed"

    def test_missing_required_fields(self):
        with pytest.raises(ValidationError):
            UploadResponse()


class TestQueryRequest:
    def test_create_query_request(self):
        request = QueryRequest(query="テストクエリ")
        assert request.query == "テストクエリ"
        assert request.top_k == 5

    def test_custom_top_k(self):
        request = QueryRequest(query="テスト", top_k=10)
        assert request.top_k == 10

    def test_empty_query_rejected(self):
        with pytest.raises(ValidationError):
            QueryRequest(query="")

    def test_top_k_minimum(self):
        with pytest.raises(ValidationError):
            QueryRequest(query="test", top_k=0)

    def test_top_k_maximum(self):
        with pytest.raises(ValidationError):
            QueryRequest(query="test", top_k=101)


class TestQueryResultResponse:
    def test_create_query_result_response(self):
        response = QueryResultResponse(
            query="test query",
            answer="test answer",
            sources=["doc1"],
            score=0.9,
            rag_type="vector",
        )
        assert response.query == "test query"
        assert response.answer == "test answer"
        assert response.sources == ["doc1"]
        assert response.score == 0.9
        assert response.rag_type == "vector"

    def test_from_domain(self):
        result = QueryResult(
            query="test",
            answer="answer",
            sources=("src1", "src2"),
            score=0.85,
            rag_type="graph",
        )
        response = QueryResultResponse.from_domain(result)
        assert response.query == "test"
        assert response.answer == "answer"
        assert response.sources == ["src1", "src2"]
        assert response.score == 0.85
        assert response.rag_type == "graph"

    def test_score_validation_too_low(self):
        with pytest.raises(ValidationError):
            QueryResultResponse(
                query="q",
                answer="a",
                sources=[],
                score=-0.1,
                rag_type="vector",
            )

    def test_score_validation_too_high(self):
        with pytest.raises(ValidationError):
            QueryResultResponse(
                query="q",
                answer="a",
                sources=[],
                score=1.1,
                rag_type="vector",
            )


class TestVectorQueryResponse:
    def test_create_vector_query_response(self):
        response = VectorQueryResponse(
            query="test",
            results=[
                QueryResultResponse(
                    query="test",
                    answer="answer",
                    sources=["doc1"],
                    score=0.9,
                    rag_type="vector",
                )
            ],
        )
        assert response.query == "test"
        assert len(response.results) == 1

    def test_empty_results(self):
        response = VectorQueryResponse(query="test", results=[])
        assert response.results == []


class TestGraphQueryResponse:
    def test_create_graph_query_response(self):
        response = GraphQueryResponse(
            query="test",
            results=[
                QueryResultResponse(
                    query="test",
                    answer="answer",
                    sources=["doc1"],
                    score=0.8,
                    rag_type="graph",
                )
            ],
        )
        assert response.query == "test"
        assert len(response.results) == 1


class TestErrorResponse:
    def test_create_error_response(self):
        response = ErrorResponse(detail="Something went wrong")
        assert response.detail == "Something went wrong"

    def test_missing_detail(self):
        with pytest.raises(ValidationError):
            ErrorResponse()
