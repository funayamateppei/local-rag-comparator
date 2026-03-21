"""Tests for the query router."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.application.use_cases.compare_rag import CompareRAGUseCase, ComparisonResult
from src.domain.models.query_result import QueryResult
from src.interfaces.routers.query import get_compare_rag_use_case, router


@pytest.fixture
def mock_use_case():
    return AsyncMock(spec=CompareRAGUseCase)


@pytest.fixture
def app(mock_use_case):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_compare_rag_use_case] = lambda: mock_use_case
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def sample_vector_result():
    return QueryResult(
        query="test query",
        answer="vector answer",
        sources=("doc1",),
        score=0.9,
        rag_type="vector",
    )


@pytest.fixture
def sample_graph_result():
    return QueryResult(
        query="test query",
        answer="graph answer",
        sources=("doc2",),
        score=0.8,
        rag_type="graph",
    )


class TestVectorQueryRouter:
    def test_vector_query_success(self, client, mock_use_case, sample_vector_result):
        mock_use_case.execute.return_value = ComparisonResult(
            query="test query",
            vector_results=[sample_vector_result],
            graph_results=[],
        )

        response = client.post(
            "/api/query/vector",
            json={"query": "test query", "top_k": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test query"
        assert len(data["results"]) == 1
        assert data["results"][0]["rag_type"] == "vector"
        assert data["results"][0]["score"] == 0.9
        mock_use_case.execute.assert_called_once_with("test query", top_k=5)

    def test_vector_query_empty_query_returns_422(self, client):
        response = client.post(
            "/api/query/vector",
            json={"query": ""},
        )
        assert response.status_code == 422

    def test_vector_query_missing_query_returns_422(self, client):
        response = client.post(
            "/api/query/vector",
            json={},
        )
        assert response.status_code == 422

    def test_vector_query_error_returns_500(self, client, mock_use_case):
        mock_use_case.execute.side_effect = Exception("Search failed")

        response = client.post(
            "/api/query/vector",
            json={"query": "test query"},
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_vector_query_custom_top_k(self, client, mock_use_case):
        mock_use_case.execute.return_value = ComparisonResult(
            query="test",
            vector_results=[],
        )

        response = client.post(
            "/api/query/vector",
            json={"query": "test", "top_k": 10},
        )

        assert response.status_code == 200
        mock_use_case.execute.assert_called_once_with("test", top_k=10)


class TestGraphQueryRouter:
    def test_graph_query_success(self, client, mock_use_case, sample_graph_result):
        mock_use_case.execute.return_value = ComparisonResult(
            query="test query",
            vector_results=[],
            graph_results=[sample_graph_result],
        )

        response = client.post(
            "/api/query/graph",
            json={"query": "test query", "top_k": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test query"
        assert len(data["results"]) == 1
        assert data["results"][0]["rag_type"] == "graph"
        assert data["results"][0]["score"] == 0.8
        mock_use_case.execute.assert_called_once_with("test query", top_k=5)

    def test_graph_query_empty_query_returns_422(self, client):
        response = client.post(
            "/api/query/graph",
            json={"query": ""},
        )
        assert response.status_code == 422

    def test_graph_query_error_returns_500(self, client, mock_use_case):
        mock_use_case.execute.side_effect = Exception("Graph search failed")

        response = client.post(
            "/api/query/graph",
            json={"query": "test query"},
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
